"""DeepSeek model wrapper implementation."""

import logging
import re
from typing import AsyncIterator, Optional, Any, Dict, List

import tiktoken
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..config.model_config import ModelConfig
from .base import BaseModelWrapper, ModelResponse, StreamChunk

logger = logging.getLogger(__name__)





def _add_reasoning_content_to_messages_helper(messages):
    """Helper function to add reasoning_content to messages.
    
    This function ensures all assistant messages with tool_calls have reasoning_content,
    which is required by DeepSeek API. It handles both dict and BaseMessage formats.
    
    This is a standalone function that can be used by all code paths to ensure
    consistent message processing.
    
    IMPORTANT: For BaseMessage objects, we modify them in-place to preserve all fields
    (like tool_call_id for ToolMessage). Only dict messages are converted.
    
    Args:
        messages: List of message dicts or BaseMessage objects
        
    Returns:
        Modified list of messages (dict messages remain as dict, BaseMessage objects remain as BaseMessage)
    """
    modified = []
    for i, msg in enumerate(messages):
        # Handle dict format (most common in API calls)
        if isinstance(msg, dict):
            msg_copy = msg.copy()
            role = msg_copy.get("role")
            tool_calls = msg_copy.get("tool_calls")
            
            # Log message details for debugging
            logger.debug(f"处理消息索引 {i}: role={role}, has_tool_calls={bool(tool_calls)}, has_reasoning={bool(msg_copy.get('reasoning_content'))}")
            
            # CRITICAL: Add reasoning_content for ALL assistant messages with tool_calls
            # DeepSeek API requires this field when tool_calls are present
            if role == "assistant" and tool_calls:
                if "reasoning_content" not in msg_copy:
                    reasoning = msg_copy.get("content", "")
                    if not reasoning or reasoning.strip() == "":
                        reasoning = "正在思考如何使用工具来回答这个问题..."
                    msg_copy["reasoning_content"] = reasoning
                    logger.info(f"✅ [消息索引 {i}] 添加 reasoning_content (工具调用: {len(tool_calls)} 个)")
                else:
                    logger.debug(f"消息索引 {i} 已有 reasoning_content")
            
            # Also check for assistant messages in tool-calling context
            # Sometimes DeepSeek requires reasoning_content even without explicit tool_calls
            # if it's part of a tool-calling conversation
            elif role == "assistant" and i > 0:
                # Check if previous messages indicate tool-calling context
                prev_msg = messages[i-1] if i > 0 else None
                if isinstance(prev_msg, dict) and prev_msg.get("role") == "assistant" and prev_msg.get("tool_calls"):
                    # This might be a follow-up assistant message in tool-calling flow
                    if "reasoning_content" not in msg_copy:
                        reasoning = msg_copy.get("content", "")
                        if not reasoning or reasoning.strip() == "":
                            reasoning = "正在处理工具调用结果..."
                        msg_copy["reasoning_content"] = reasoning
                        logger.info(f"✅ [消息索引 {i}] 添加上下文 reasoning_content (工具调用流程)")
            
            modified.append(msg_copy)
        
        # Handle BaseMessage format (from LangChain)
        elif isinstance(msg, BaseMessage):
            # IMPORTANT: For BaseMessage, we should modify the object directly
            # instead of converting to dict, to preserve all fields (like tool_call_id for ToolMessage)
            
            # Only process AIMessage with tool_calls
            if isinstance(msg, AIMessage):
                # Extract tool_calls
                tool_calls = None
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls = msg.tool_calls
                elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                    tool_calls = msg.additional_kwargs.get('tool_calls')
                
                # Check for existing reasoning_content
                existing_reasoning = None
                if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                    existing_reasoning = msg.additional_kwargs.get('reasoning_content')
                
                # CRITICAL: Add reasoning_content for ALL assistant messages with tool_calls
                if tool_calls:
                    if not existing_reasoning:
                        # Initialize additional_kwargs if needed
                        if not hasattr(msg, 'additional_kwargs') or msg.additional_kwargs is None:
                            msg.additional_kwargs = {}
                        
                        reasoning = msg.content if hasattr(msg, 'content') and msg.content else ""
                        if not reasoning or reasoning.strip() == "":
                            reasoning = "正在思考如何使用工具来回答这个问题..."
                        
                        msg.additional_kwargs['reasoning_content'] = reasoning
                        # Log tool_calls count for debugging
                        tool_calls_count = len(tool_calls) if isinstance(tool_calls, list) else 1
                        logger.info(f"✅ [消息索引 {i}] BaseMessage 对象添加 reasoning_content (工具调用: {tool_calls_count} 个)")
                        logger.debug(f"   reasoning_content 内容: {reasoning[:100]}...")
                    else:
                        logger.debug(f"消息索引 {i} 已有 reasoning_content: {existing_reasoning[:50]}...")
            
            # For all BaseMessage objects (including ToolMessage, HumanMessage, etc.),
            # keep them as-is to preserve all fields
            modified.append(msg)
        else:
            # Unknown format, pass through (but log warning)
            logger.warning(f"⚠️ 未知消息格式在索引 {i}: {type(msg)}")
            modified.append(msg)
    
    return modified


class DeepSeekWrapper(BaseModelWrapper):
    """Wrapper for DeepSeek models using OpenAI-compatible API."""
    
    def __init__(self, config: ModelConfig):
        """Initialize DeepSeek wrapper.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        
        # Initialize OpenAI client with DeepSeek base URL
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        
        # Initialize LangChain model with DeepSeek base URL
        self.model = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            openai_api_key=config.api_key,
            openai_api_base=config.base_url,
            request_timeout=config.timeout,
        )
        
        # Use cl100k_base tokenizer (similar to GPT-4)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate a response using DeepSeek API.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional DeepSeek-specific parameters
        
        Returns:
            ModelResponse with generated content and metadata
        
        Raises:
            Exception: If API call fails after retries
        """
        try:
            # Validate context length
            is_valid, token_count = self.validate_context_length(
                prompt, system_message
            )
            if not is_valid:
                logger.warning(
                    f"Prompt length ({token_count} tokens) is close to "
                    f"context limit. Consider reducing prompt size."
                )
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Override config with kwargs if provided
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            
            # Call DeepSeek API (OpenAI-compatible)
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.config.timeout,
            )
            
            # Extract response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Model returned empty response")
            
            # Build structured response
            usage = response.usage
            return ModelResponse(
                content=content,
                model=response.model,
                tokens_used=usage.total_tokens,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                finish_reason=response.choices[0].finish_reason,
            )
        
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def generate_stream(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using DeepSeek API.
        
        For deepseek-reasoner model, yields reasoning content first, then answer.
        For deepseek-chat model, yields answer content directly.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional DeepSeek-specific parameters
        
        Yields:
            StreamChunk objects containing response text chunks with chunk_type
        
        Raises:
            Exception: If API call fails after retries
        """
        try:
            # Validate context length
            is_valid, token_count = self.validate_context_length(
                prompt, system_message
            )
            if not is_valid:
                logger.warning(
                    f"Prompt length ({token_count} tokens) is close to "
                    f"context limit. Consider reducing prompt size."
                )
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # CRITICAL: Process messages to ensure all assistant messages with tool_calls have reasoning_content
            # This is required by DeepSeek API when tool_calls are present
            messages = _add_reasoning_content_to_messages_helper(messages)
            
            # Override config with kwargs if provided
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            
            # Call DeepSeek API with streaming
            # Wrap in try-except to handle reasoning_content errors and retry
            try:
                stream = self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.config.timeout,
                    stream=True,
                )
            except Exception as e:
                error_str = str(e)
                # If we get reasoning_content error, try more aggressive fix
                if "reasoning_content" in error_str.lower():
                    logger.warning(f"⚠️ [generate_stream] 遇到 reasoning_content 错误，尝试修复")
                    logger.debug(f"错误详情: {error_str[:300]}")
                    
                    # More aggressive fix: ensure ALL assistant messages have reasoning_content
                    for i, msg in enumerate(messages):
                        if isinstance(msg, dict) and msg.get("role") == "assistant":
                            if msg.get("tool_calls") and "reasoning_content" not in msg:
                                reasoning = msg.get("content", "")
                                if not reasoning or reasoning.strip() == "":
                                    reasoning = "正在思考如何使用工具来回答这个问题..."
                                msg["reasoning_content"] = reasoning
                                logger.info(f"✅ [generate_stream-错误修复-消息 {i}] 强制添加 reasoning_content")
                    
                    # Retry with fixed messages
                    stream = self.client.chat.completions.create(
                        model=self.config.model_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=self.config.timeout,
                        stream=True,
                    )
                else:
                    raise
            
            # Check if this is a reasoner model
            is_reasoner = self.config.model_variant == "deepseek-reasoner"
            
            # Stream response chunks
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Handle reasoning content (only for deepseek-reasoner)
                if is_reasoner and hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    yield StreamChunk(
                        content=delta.reasoning_content,
                        finish_reason=None,
                        chunk_type="reasoning",
                    )
                
                # Handle answer content
                if delta.content:
                    yield StreamChunk(
                        content=delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                        chunk_type="answer",
                    )
        
        except Exception as e:
            logger.error(f"DeepSeek streaming call failed: {str(e)}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))
    
    def get_langchain_llm(self):
        """Get LangChain compatible LLM instance with DeepSeek reasoning_content support.
        
        Returns:
            LangChain ChatOpenAI instance configured for DeepSeek
        """
        # Create a custom ChatOpenAI subclass that handles reasoning_content
        class DeepSeekChatOpenAI(ChatOpenAI):
            """Custom ChatOpenAI that adds reasoning_content for DeepSeek API."""
            
            def _add_reasoning_content_to_messages(self, messages):
                """Helper method to add reasoning_content to messages.
                
                This method ensures all assistant messages with tool_calls have reasoning_content,
                which is required by DeepSeek API. It handles both dict and BaseMessage formats.
                
                Args:
                    messages: List of message dicts or BaseMessage objects
                    
                Returns:
                    Modified list of messages
                """
                modified = []
                for i, msg in enumerate(messages):
                    # Handle dict format (most common in API calls)
                    if isinstance(msg, dict):
                        msg_copy = msg.copy()
                        role = msg_copy.get("role")
                        tool_calls = msg_copy.get("tool_calls")
                        
                        # Log message details for debugging
                        logger.debug(f"处理消息索引 {i}: role={role}, has_tool_calls={bool(tool_calls)}, has_reasoning={bool(msg_copy.get('reasoning_content'))}")
                        
                        # CRITICAL: Add reasoning_content for ALL assistant messages with tool_calls
                        # DeepSeek API requires this field when tool_calls are present
                        if role == "assistant" and tool_calls:
                            if "reasoning_content" not in msg_copy:
                                reasoning = msg_copy.get("content", "")
                                if not reasoning or reasoning.strip() == "":
                                    reasoning = "正在思考如何使用工具来回答这个问题..."
                                msg_copy["reasoning_content"] = reasoning
                                logger.info(f"✅ [消息索引 {i}] 添加 reasoning_content (工具调用: {len(tool_calls)} 个)")
                            else:
                                logger.debug(f"消息索引 {i} 已有 reasoning_content")
                        
                        # Also check for assistant messages in tool-calling context
                        # Sometimes DeepSeek requires reasoning_content even without explicit tool_calls
                        # if it's part of a tool-calling conversation
                        elif role == "assistant" and i > 0:
                            # Check if previous messages indicate tool-calling context
                            prev_msg = messages[i-1] if i > 0 else None
                            if isinstance(prev_msg, dict) and prev_msg.get("role") == "assistant" and prev_msg.get("tool_calls"):
                                # This might be a follow-up assistant message in tool-calling flow
                                if "reasoning_content" not in msg_copy:
                                    reasoning = msg_copy.get("content", "")
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在处理工具调用结果..."
                                    msg_copy["reasoning_content"] = reasoning
                                    logger.info(f"✅ [消息索引 {i}] 添加上下文 reasoning_content (工具调用流程)")
                        
                        modified.append(msg_copy)
                    
                    # Handle BaseMessage format (from LangChain)
                    elif isinstance(msg, BaseMessage):
                        # IMPORTANT: For BaseMessage, we should modify the object directly
                        # instead of converting to dict, to preserve all fields (like tool_call_id for ToolMessage)
                        
                        # Only process AIMessage with tool_calls
                        if isinstance(msg, AIMessage):
                            # Extract tool_calls
                            tool_calls = None
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                tool_calls = msg.tool_calls
                            elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                tool_calls = msg.additional_kwargs.get('tool_calls')
                            
                            # Check for existing reasoning_content
                            existing_reasoning = None
                            if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                existing_reasoning = msg.additional_kwargs.get('reasoning_content')
                            
                            # CRITICAL: Add reasoning_content for ALL assistant messages with tool_calls
                            if tool_calls:
                                if not existing_reasoning:
                                    # Initialize additional_kwargs if needed
                                    if not hasattr(msg, 'additional_kwargs') or msg.additional_kwargs is None:
                                        msg.additional_kwargs = {}
                                    
                                    reasoning = msg.content if hasattr(msg, 'content') and msg.content else ""
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在思考如何使用工具来回答这个问题..."
                                    
                                    msg.additional_kwargs['reasoning_content'] = reasoning
                                    # Log tool_calls count for debugging
                                    tool_calls_count = len(tool_calls) if isinstance(tool_calls, list) else 1
                                    logger.info(f"✅ [消息索引 {i}] BaseMessage 对象添加 reasoning_content (工具调用: {tool_calls_count} 个)")
                                    logger.debug(f"   reasoning_content 内容: {reasoning[:100]}...")
                                else:
                                    logger.debug(f"消息索引 {i} 已有 reasoning_content: {existing_reasoning[:50]}...")
                        
                        # For all BaseMessage objects (including ToolMessage, HumanMessage, etc.),
                        # keep them as-is to preserve all fields
                        modified.append(msg)
                    else:
                        # Unknown format, pass through
                        modified.append(msg)
                
                return modified
            
            def _wrap_client_create(self, original_create):
                """Create a wrapper for client.create method.
                
                Args:
                    original_create: Original create method
                    
                Returns:
                    Wrapped create method
                """
                def wrapped_create(*args, **create_kwargs):
                    """Wrapper that adds reasoning_content to messages."""
                    if "messages" in create_kwargs:
                        create_kwargs["messages"] = self._add_reasoning_content_to_messages(
                            create_kwargs["messages"]
                        )
                    
                    try:
                        return original_create(*args, **create_kwargs)
                    except Exception as e:
                        error_str = str(e)
                        # If we still get reasoning_content error, try more aggressive fix
                        if "reasoning_content" in error_str.lower() and "messages" in create_kwargs:
                            logger.warning(f"⚠️ 仍然遇到 reasoning_content 错误，尝试更激进的修复")
                            logger.debug(f"错误详情: {error_str[:200]}")
                            
                            # Try to fix ALL assistant messages, not just those with tool_calls
                            msgs = create_kwargs["messages"]
                            for i, msg in enumerate(msgs):
                                if isinstance(msg, dict) and msg.get("role") == "assistant":
                                    if "reasoning_content" not in msg:
                                        reasoning = msg.get("content", "")
                                        if not reasoning or reasoning.strip() == "":
                                            reasoning = "正在思考中..."
                                        msg["reasoning_content"] = reasoning
                                        logger.info(f"✅ [错误修复] 消息索引 {i} 强制添加 reasoning_content")
                            
                            # Retry with fixed messages
                            return original_create(*args, **create_kwargs)
                        raise
                
                return wrapped_create
            
            def _generate(self, messages, stop=None, run_manager=None, **kwargs):
                """Override _generate to add reasoning_content before API call."""
                # Process messages before passing to parent
                if isinstance(messages, list):
                    messages = _add_reasoning_content_to_messages_helper(messages)
                
                original_create = self.client.create
                wrapped_create = self._wrap_client_create(original_create)
                
                # Replace create method temporarily
                self.client.create = wrapped_create
                try:
                    return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
                finally:
                    # Restore original
                    self.client.create = original_create
            
            async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
                """Override _agenerate to add reasoning_content before async API call."""
                # CRITICAL: Process messages BEFORE passing to parent
                # This ensures reasoning_content is added to BaseMessage objects before formatting
                if isinstance(messages, list):
                    messages = _add_reasoning_content_to_messages_helper(messages)
                
                # CRITICAL: Also ensure _format_messages will be called with proper reasoning_content
                # by wrapping the client's chat.completions.create method
                original_create = self.client.create
                wrapped_create = self._wrap_client_create(original_create)
                
                # Replace create method temporarily
                self.client.create = wrapped_create
                try:
                    # Call parent's _agenerate which will call _format_messages
                    # _format_messages will ensure reasoning_content is in the final dict format
                    return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
                finally:
                    # Restore original
                    self.client.create = original_create
            
            def _format_messages(self, messages):
                """Override _format_messages to add reasoning_content before formatting.
                
                This is called by LangChain to convert messages to API format.
                We intercept here to ensure reasoning_content is added.
                """
                # Convert messages to list if needed
                if not isinstance(messages, list):
                    messages = list(messages)
                
                # Process messages to add reasoning_content
                processed_messages = _add_reasoning_content_to_messages_helper(messages)
                
                # CRITICAL: Build a mapping of tool_calls to reasoning_content BEFORE formatting
                # This ensures we can match messages even if LangChain filters or reorders them
                tool_calls_to_reasoning = {}
                for msg in processed_messages:
                    if isinstance(msg, AIMessage):
                        tool_calls = None
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            tool_calls = msg.tool_calls
                        elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                            tool_calls = msg.additional_kwargs.get('tool_calls')
                        
                        if tool_calls:
                            # Use tool_calls as key (convert to string for hashing)
                            tool_calls_key = str(tool_calls)
                            reasoning = None
                            if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                reasoning = msg.additional_kwargs.get('reasoning_content')
                            if not reasoning and hasattr(msg, 'content') and msg.content:
                                reasoning = msg.content
                            if not reasoning or reasoning.strip() == "":
                                reasoning = "正在思考如何使用工具来回答这个问题..."
                            tool_calls_to_reasoning[tool_calls_key] = reasoning
                            logger.debug(f"🔍 [_format_messages] 建立映射: tool_calls -> reasoning_content (长度: {len(reasoning)})")
                
                # Call parent method with processed messages
                # Parent will convert BaseMessage to dict, but may not extract reasoning_content from additional_kwargs
                formatted = super()._format_messages(processed_messages)
                
                # Ensure reasoning_content from additional_kwargs is extracted to dict format
                # LangChain's _format_messages should handle this, but we ensure it here
                if isinstance(formatted, list):
                    for i, msg_dict in enumerate(formatted):
                        if isinstance(msg_dict, dict) and msg_dict.get("role") == "assistant":
                            # If we have tool_calls but no reasoning_content, check if it's in the original message
                            if msg_dict.get("tool_calls") and "reasoning_content" not in msg_dict:
                                # CRITICAL: We MUST add reasoning_content for tool_calls
                                # Try to find reasoning_content in the original message
                                reasoning = None
                                
                                # Match by index first (most reliable)
                                logger.debug(f"🔍 [_format_messages] 尝试匹配消息索引 {i}，processed_messages 长度: {len(processed_messages)}")
                                if i < len(processed_messages):
                                    orig_msg = processed_messages[i]
                                    logger.debug(f"  原始消息类型: {type(orig_msg)}")
                                    if isinstance(orig_msg, AIMessage):
                                        # Check additional_kwargs first
                                        if hasattr(orig_msg, 'additional_kwargs') and orig_msg.additional_kwargs:
                                            reasoning = orig_msg.additional_kwargs.get('reasoning_content')
                                            logger.debug(f"  从 additional_kwargs 提取 reasoning: {bool(reasoning)}")
                                        # If not found, use content as reasoning
                                        if not reasoning and hasattr(orig_msg, 'content') and orig_msg.content:
                                            reasoning = orig_msg.content
                                            logger.debug(f"  使用 content 作为 reasoning: {bool(reasoning)}")
                                else:
                                    logger.warning(f"⚠️ 消息索引 {i} 超出 processed_messages 范围")
                                
                                # If still not found, try to match by tool_calls using our mapping
                                if not reasoning:
                                    tool_calls_key = str(tool_calls)
                                    if tool_calls_key in tool_calls_to_reasoning:
                                        reasoning = tool_calls_to_reasoning[tool_calls_key]
                                        logger.debug(f"✅ [_format_messages] 通过 tool_calls 映射找到 reasoning_content")
                                
                                # If still not found, search all messages by tool_calls match
                                if not reasoning:
                                    for orig_msg in processed_messages:
                                        if isinstance(orig_msg, AIMessage):
                                            # Check if this message has tool_calls (match by tool_calls)
                                            orig_tool_calls = None
                                            if hasattr(orig_msg, 'tool_calls') and orig_msg.tool_calls:
                                                orig_tool_calls = orig_msg.tool_calls
                                            elif hasattr(orig_msg, 'additional_kwargs') and orig_msg.additional_kwargs:
                                                orig_tool_calls = orig_msg.additional_kwargs.get('tool_calls')
                                            
                                            # If tool_calls match, extract reasoning_content
                                            if orig_tool_calls and len(orig_tool_calls) == len(tool_calls):
                                                if hasattr(orig_msg, 'additional_kwargs') and orig_msg.additional_kwargs:
                                                    reasoning = orig_msg.additional_kwargs.get('reasoning_content')
                                                if not reasoning and hasattr(orig_msg, 'content') and orig_msg.content:
                                                    reasoning = orig_msg.content
                                                if reasoning:
                                                    logger.debug(f"✅ [_format_messages] 通过遍历找到 reasoning_content")
                                                    break
                                
                                # If still no reasoning, use default
                                if not reasoning or reasoning.strip() == "":
                                    reasoning = "正在思考如何使用工具来回答这个问题..."
                                
                                msg_dict["reasoning_content"] = reasoning
                                logger.info(f"✅ [_format_messages] 消息索引 {i} 强制添加 reasoning_content (工具调用: {len(tool_calls)} 个)")
                
                return formatted
            
            async def _astream(self, messages, stop=None, run_manager=None, **kwargs):
                """Override _astream to add reasoning_content before streaming API call."""
                # CRITICAL: Process messages BEFORE passing to parent
                # This ensures reasoning_content is added to BaseMessage objects before formatting
                if isinstance(messages, list):
                    messages = _add_reasoning_content_to_messages_helper(messages)
                
                # Also ensure _format_messages will be called with proper reasoning_content
                # by wrapping the client's chat.completions.create method
                original_create = self.client.create
                wrapped_create = self._wrap_client_create(original_create)
                
                # Replace create method temporarily
                self.client.create = wrapped_create
                try:
                    async for chunk in super()._astream(messages, stop=stop, run_manager=run_manager, **kwargs):
                        yield chunk
                finally:
                    # Restore original
                    self.client.create = original_create
            
            async def astream(self, input, config=None, **kwargs):
                """Override astream to add reasoning_content before streaming API call.
                
                This is called by LangGraph, so we need to intercept here too.
                LangGraph may pass messages in different formats, so we need to handle them.
                """
                # CRITICAL: Process messages BEFORE LangGraph processes them
                # LangGraph may pass messages as dict or list, handle both cases
                if isinstance(input, dict) and "messages" in input:
                    input["messages"] = _add_reasoning_content_to_messages_helper(input["messages"])
                    logger.debug(f"🔍 [astream] 处理了 {len(input['messages'])} 条消息 (dict格式)")
                elif isinstance(input, list):
                    # Input might be a list of messages
                    input = _add_reasoning_content_to_messages_helper(input)
                    logger.debug(f"🔍 [astream] 处理了 {len(input)} 条消息 (list格式)")
                
                # Wrap client methods to ensure reasoning_content is added at API call time
                original_create = self.client.create
                wrapped_create = self._wrap_client_create(original_create)
                
                # Replace create method temporarily
                self.client.create = wrapped_create
                try:
                    async for chunk in super().astream(input, config=config, **kwargs):
                        yield chunk
                finally:
                    # Restore original
                    self.client.create = original_create
        
        # Get LangSmith callbacks if enabled
        callbacks = self._get_callbacks()
        
        # Create new instance with same configuration
        wrapped_model = DeepSeekChatOpenAI(
            model=self.model.model_name,
            temperature=self.model.temperature,
            max_tokens=self.model.max_tokens,
            openai_api_key=self.model.openai_api_key,
            openai_api_base=self.model.openai_api_base,
            request_timeout=self.model.request_timeout,
            callbacks=callbacks if callbacks else None,
        )
        
        # Also wrap the client's create method proactively for additional safety
        # This ensures all API calls (sync, async, streaming) are intercepted
        original_create = wrapped_model.client.create
        
        def proactive_wrapped_create(*args, **kwargs):
            """Proactively add reasoning_content before API call.
            
            This wrapper ensures all assistant messages with tool_calls have reasoning_content
            before the API call is made, preventing errors from DeepSeek API.
            """
            if "messages" in kwargs:
                # Use the standalone helper function for consistent processing
                kwargs["messages"] = _add_reasoning_content_to_messages_helper(kwargs["messages"])
                
                # Verify all assistant messages with tool_calls have reasoning_content
                for i, msg in enumerate(kwargs["messages"]):
                    if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("tool_calls"):
                        if "reasoning_content" not in msg:
                            logger.warning(f"⚠️ [主动包装-验证失败] 消息索引 {i} 仍然缺少 reasoning_content，强制添加")
                            msg["reasoning_content"] = msg.get("content", "正在思考如何使用工具来回答这个问题...")
            
            try:
                return original_create(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                # If we still get reasoning_content error, try more aggressive fix
                if "reasoning_content" in error_str.lower() and "messages" in kwargs:
                    logger.warning(f"⚠️ [主动包装] 仍然遇到 reasoning_content 错误，尝试更激进的修复")
                    logger.debug(f"错误详情: {error_str[:300]}")
                    
                    # More aggressive fix: ensure ALL assistant messages with tool_calls have reasoning_content
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, dict) and msg.get("role") == "assistant":
                            if msg.get("tool_calls") and "reasoning_content" not in msg:
                                msg["reasoning_content"] = msg.get("content", "正在思考如何使用工具来回答这个问题...")
                                logger.info(f"✅ [主动包装-错误修复-消息 {i}] 强制添加 reasoning_content")
                    
                    logger.info(f"✅ [主动包装-错误修复] 已修复所有消息的 reasoning_content")
                    
                    # Retry with fixed messages
                    return original_create(*args, **kwargs)
                raise
        
        # Replace create method permanently at client level
        wrapped_model.client.create = proactive_wrapped_create
        
        # Also wrap chat.completions.create if it exists (more direct path)
        # This is the actual method called by LangChain ChatOpenAI
        if hasattr(wrapped_model.client, 'chat') and hasattr(wrapped_model.client.chat, 'completions'):
            original_chat_create = wrapped_model.client.chat.completions.create
            
            def wrapped_chat_create(*args, **kwargs):
                """Wrapper for chat.completions.create that adds reasoning_content.
                
                This is the direct path used by LangChain ChatOpenAI, so we need to intercept here.
                """
                if "messages" in kwargs:
                    # Log message details before processing
                    logger.debug(f"🔍 [chat.completions.create] 处理 {len(kwargs['messages'])} 条消息")
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, dict):
                            role = msg.get("role")
                            has_tool_calls = bool(msg.get("tool_calls"))
                            has_reasoning = bool(msg.get("reasoning_content"))
                            logger.debug(f"  消息 {i}: role={role}, tool_calls={has_tool_calls}, reasoning={has_reasoning}")
                        elif isinstance(msg, BaseMessage):
                            role = getattr(msg, 'role', getattr(msg, 'type', 'unknown'))
                            has_tool_calls = bool(getattr(msg, 'tool_calls', None))
                            has_reasoning = bool(getattr(msg, 'additional_kwargs', {}).get('reasoning_content') if hasattr(msg, 'additional_kwargs') else False)
                            logger.debug(f"  消息 {i}: role={role}, tool_calls={has_tool_calls}, reasoning={has_reasoning}")
                    
                    # CRITICAL: Process messages to add reasoning_content
                    kwargs["messages"] = _add_reasoning_content_to_messages_helper(kwargs["messages"])
                    
                    # CRITICAL: Convert BaseMessage to dict format BEFORE API call
                    # LangChain may pass BaseMessage objects, but API needs dict format
                    processed_msgs = []
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, BaseMessage):
                            # Convert BaseMessage to dict format
                            if isinstance(msg, AIMessage):
                                msg_dict = {
                                    "role": "assistant",
                                    "content": msg.content if hasattr(msg, 'content') else "",
                                }
                            elif isinstance(msg, ToolMessage):
                                msg_dict = {
                                    "role": "tool",
                                    "content": msg.content if hasattr(msg, 'content') else "",
                                }
                                # ToolMessage needs tool_call_id
                                if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
                                    msg_dict["tool_call_id"] = msg.tool_call_id
                            else:
                                # HumanMessage or other types
                                msg_dict = {
                                    "role": "user",
                                    "content": msg.content if hasattr(msg, 'content') else "",
                                }
                            
                            # Extract tool_calls if present (for AIMessage)
                            if isinstance(msg, AIMessage):
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    msg_dict["tool_calls"] = msg.tool_calls
                                elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                    tool_calls = msg.additional_kwargs.get('tool_calls')
                                    if tool_calls:
                                        msg_dict["tool_calls"] = tool_calls
                                
                                # Extract reasoning_content from additional_kwargs
                                if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                    reasoning = msg.additional_kwargs.get('reasoning_content')
                                    if reasoning:
                                        msg_dict["reasoning_content"] = reasoning
                                        logger.debug(f"🔍 [消息索引 {i}] 从 additional_kwargs 提取 reasoning_content (长度: {len(reasoning)})")
                            
                            # CRITICAL: If tool_calls exist but no reasoning_content, add it
                            if msg_dict.get("tool_calls") and "reasoning_content" not in msg_dict:
                                reasoning = msg_dict.get("content", "")
                                if not reasoning or reasoning.strip() == "":
                                    reasoning = "正在思考如何使用工具来回答这个问题..."
                                msg_dict["reasoning_content"] = reasoning
                                logger.info(f"✅ [chat.completions.create] 消息索引 {i} BaseMessage转dict后添加 reasoning_content")
                            
                            processed_msgs.append(msg_dict)
                        elif isinstance(msg, dict):
                            # Already dict format, but verify reasoning_content
                            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                                if "reasoning_content" not in msg:
                                    reasoning = msg.get("content", "")
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在思考如何使用工具来回答这个问题..."
                                    msg["reasoning_content"] = reasoning
                                    logger.info(f"✅ [chat.completions.create] 消息索引 {i} dict格式强制添加 reasoning_content")
                            processed_msgs.append(msg)
                        else:
                            processed_msgs.append(msg)
                    
                    kwargs["messages"] = processed_msgs
                    
                    # Final verification: ensure all assistant messages with tool_calls have reasoning_content
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, dict) and msg.get("role") == "assistant":
                            tool_calls = msg.get("tool_calls")
                            if tool_calls:
                                if "reasoning_content" not in msg:
                                    logger.warning(f"⚠️ [最终验证失败] 消息索引 {i} 仍然缺少 reasoning_content，强制添加")
                                    reasoning = msg.get("content", "")
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在思考如何使用工具来回答这个问题..."
                                    msg["reasoning_content"] = reasoning
                                    logger.info(f"✅ [最终修复] 消息索引 {i} 已添加 reasoning_content")
                    
                    # Log final state before API call
                    logger.debug(f"🔍 [chat.completions.create] API调用前最终检查:")
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, dict):
                            role = msg.get("role")
                            tool_calls = msg.get("tool_calls")
                            reasoning = msg.get("reasoning_content")
                            logger.debug(f"  消息 {i}: role={role}, tool_calls={bool(tool_calls)}, reasoning={bool(reasoning)}")
                            if role == "assistant" and tool_calls and not reasoning:
                                logger.error(f"❌ [严重错误] 消息索引 {i} 有 tool_calls 但缺少 reasoning_content！")
                
                try:
                    return original_chat_create(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    if "reasoning_content" in error_str.lower() and "messages" in kwargs:
                        logger.warning(f"⚠️ [chat.completions.create] 遇到 reasoning_content 错误，尝试修复")
                        logger.debug(f"错误详情: {error_str[:300]}")
                        
                        # More aggressive fix: ensure ALL assistant messages have reasoning_content
                        # Check for message index in error message to identify the problematic message
                        index_match = re.search(r'message index (\d+)', error_str.lower())
                        if index_match:
                            problem_index = int(index_match.group(1))
                            logger.info(f"🔍 错误信息指出问题在消息索引 {problem_index}")
                        
                        # Fix ALL assistant messages with tool_calls, not just the one mentioned
                        for i, msg in enumerate(kwargs["messages"]):
                            if isinstance(msg, dict) and msg.get("role") == "assistant":
                                if msg.get("tool_calls") and "reasoning_content" not in msg:
                                    reasoning = msg.get("content", "")
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在思考如何使用工具来回答这个问题..."
                                    msg["reasoning_content"] = reasoning
                                    logger.info(f"✅ [错误修复-消息 {i}] 强制添加 reasoning_content")
                            elif isinstance(msg, BaseMessage) and isinstance(msg, AIMessage):
                                # Handle BaseMessage format
                                tool_calls = None
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    tool_calls = msg.tool_calls
                                elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                    tool_calls = msg.additional_kwargs.get('tool_calls')
                                
                                if tool_calls:
                                    if not hasattr(msg, 'additional_kwargs') or msg.additional_kwargs is None:
                                        msg.additional_kwargs = {}
                                    if 'reasoning_content' not in msg.additional_kwargs:
                                        reasoning = msg.content if hasattr(msg, 'content') and msg.content else ""
                                        if not reasoning or reasoning.strip() == "":
                                            reasoning = "正在思考如何使用工具来回答这个问题..."
                                        msg.additional_kwargs['reasoning_content'] = reasoning
                                        logger.info(f"✅ [错误修复-消息 {i}] BaseMessage 强制添加 reasoning_content")
                        
                        # Re-process messages after fixing
                        kwargs["messages"] = _add_reasoning_content_to_messages_helper(kwargs["messages"])
                        
                        logger.info(f"✅ [chat.completions.create-错误修复] 已修复所有消息的 reasoning_content")
                        return original_chat_create(*args, **kwargs)
                    raise
            
            wrapped_model.client.chat.completions.create = wrapped_chat_create
        
        # CRITICAL: Also wrap async_client (used by _agenerate)
        # LangChain ChatOpenAI uses self.async_client which points to root_async_client.chat.completions
        # So we need to wrap the 'create' method on async_client object directly
        if hasattr(wrapped_model, 'async_client') and hasattr(wrapped_model.async_client, 'create'):
            original_async_chat_create = wrapped_model.async_client.create
            
            async def wrapped_async_chat_create(*args, **kwargs):
                """Async wrapper for chat.completions.create that adds reasoning_content.
                
                This is the async path used by LangChain ChatOpenAI's _agenerate, so we need to intercept here.
                """
                if "messages" in kwargs:
                    # Log message details before processing
                    logger.info(f"🔍 [async_chat.completions.create] 处理 {len(kwargs['messages'])} 条消息")
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, dict):
                            role = msg.get("role")
                            has_tool_calls = bool(msg.get("tool_calls"))
                            has_reasoning = bool(msg.get("reasoning_content"))
                            logger.info(f"  消息 {i}: role={role}, tool_calls={has_tool_calls}, reasoning={has_reasoning}")
                        elif isinstance(msg, BaseMessage):
                            role = getattr(msg, 'role', getattr(msg, 'type', 'unknown'))
                            has_tool_calls = bool(getattr(msg, 'tool_calls', None))
                            has_reasoning = bool(getattr(msg, 'additional_kwargs', {}).get('reasoning_content') if hasattr(msg, 'additional_kwargs') else False)
                            logger.info(f"  消息 {i}: role={role}, tool_calls={has_tool_calls}, reasoning={has_reasoning}")
                    
                    # CRITICAL: Process messages to add reasoning_content
                    kwargs["messages"] = _add_reasoning_content_to_messages_helper(kwargs["messages"])
                    
                    # CRITICAL: Convert BaseMessage to dict format BEFORE API call
                    # LangChain may pass BaseMessage objects, but API needs dict format
                    processed_msgs = []
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, BaseMessage):
                            # Convert BaseMessage to dict format
                            if isinstance(msg, AIMessage):
                                msg_dict = {
                                    "role": "assistant",
                                    "content": msg.content if hasattr(msg, 'content') else "",
                                }
                            elif isinstance(msg, ToolMessage):
                                msg_dict = {
                                    "role": "tool",
                                    "content": msg.content if hasattr(msg, 'content') else "",
                                }
                                # ToolMessage needs tool_call_id
                                if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
                                    msg_dict["tool_call_id"] = msg.tool_call_id
                            else:
                                # HumanMessage or other types
                                msg_dict = {
                                    "role": "user",
                                    "content": msg.content if hasattr(msg, 'content') else "",
                                }
                            
                            # Extract tool_calls if present (for AIMessage)
                            if isinstance(msg, AIMessage):
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    msg_dict["tool_calls"] = msg.tool_calls
                                elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                    tool_calls = msg.additional_kwargs.get('tool_calls')
                                    if tool_calls:
                                        msg_dict["tool_calls"] = tool_calls
                                
                                # Extract reasoning_content from additional_kwargs
                                if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                    reasoning = msg.additional_kwargs.get('reasoning_content')
                                    if reasoning:
                                        msg_dict["reasoning_content"] = reasoning
                                        logger.debug(f"🔍 [async-消息索引 {i}] 从 additional_kwargs 提取 reasoning_content (长度: {len(reasoning)})")
                            
                            # CRITICAL: If tool_calls exist but no reasoning_content, add it
                            if msg_dict.get("tool_calls") and "reasoning_content" not in msg_dict:
                                reasoning = msg_dict.get("content", "")
                                if not reasoning or reasoning.strip() == "":
                                    reasoning = "正在思考如何使用工具来回答这个问题..."
                                msg_dict["reasoning_content"] = reasoning
                                logger.info(f"✅ [async_chat.completions.create] 消息索引 {i} BaseMessage转dict后添加 reasoning_content")
                            
                            processed_msgs.append(msg_dict)
                        elif isinstance(msg, dict):
                            # Already dict format, but verify reasoning_content
                            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                                if "reasoning_content" not in msg:
                                    reasoning = msg.get("content", "")
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在思考如何使用工具来回答这个问题..."
                                    msg["reasoning_content"] = reasoning
                                    logger.info(f"✅ [async_chat.completions.create] 消息索引 {i} dict格式强制添加 reasoning_content")
                            processed_msgs.append(msg)
                        else:
                            processed_msgs.append(msg)
                    
                    kwargs["messages"] = processed_msgs
                    
                    # Final verification: ensure all assistant messages with tool_calls have reasoning_content
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, dict) and msg.get("role") == "assistant":
                            tool_calls = msg.get("tool_calls")
                            if tool_calls:
                                if "reasoning_content" not in msg:
                                    logger.warning(f"⚠️ [async-最终验证失败] 消息索引 {i} 仍然缺少 reasoning_content，强制添加")
                                    reasoning = msg.get("content", "")
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在思考如何使用工具来回答这个问题..."
                                    msg["reasoning_content"] = reasoning
                                    logger.info(f"✅ [async-最终修复] 消息索引 {i} 已添加 reasoning_content")
                    
                    # Log final state before API call
                    logger.info(f"🔍 [async_chat.completions.create] API调用前最终检查:")
                    for i, msg in enumerate(kwargs["messages"]):
                        if isinstance(msg, dict):
                            role = msg.get("role")
                            tool_calls = msg.get("tool_calls")
                            reasoning = msg.get("reasoning_content")
                            logger.info(f"  消息 {i}: role={role}, tool_calls={bool(tool_calls)}, reasoning={bool(reasoning)}")
                            if role == "assistant" and tool_calls and not reasoning:
                                logger.error(f"❌ [严重错误] 消息索引 {i} 有 tool_calls 但缺少 reasoning_content！")
                
                try:
                    return await original_async_chat_create(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    if "reasoning_content" in error_str.lower() and "messages" in kwargs:
                        logger.warning(f"⚠️ [async_chat.completions.create] 遇到 reasoning_content 错误，尝试修复")
                        logger.debug(f"错误详情: {error_str[:300]}")
                        
                        # More aggressive fix: ensure ALL assistant messages have reasoning_content
                        # Check for message index in error message to identify the problematic message
                        index_match = re.search(r'message index (\d+)', error_str.lower())
                        if index_match:
                            problem_index = int(index_match.group(1))
                            logger.info(f"🔍 错误信息指出问题在消息索引 {problem_index}")
                        
                        # Fix ALL assistant messages with tool_calls, not just the one mentioned
                        for i, msg in enumerate(kwargs["messages"]):
                            if isinstance(msg, dict) and msg.get("role") == "assistant":
                                if msg.get("tool_calls") and "reasoning_content" not in msg:
                                    reasoning = msg.get("content", "")
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在思考如何使用工具来回答这个问题..."
                                    msg["reasoning_content"] = reasoning
                                    logger.info(f"✅ [async-错误修复-消息 {i}] 强制添加 reasoning_content")
                            elif isinstance(msg, BaseMessage) and isinstance(msg, AIMessage):
                                # Handle BaseMessage format
                                tool_calls = None
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    tool_calls = msg.tool_calls
                                elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                                    tool_calls = msg.additional_kwargs.get('tool_calls')
                                
                                if tool_calls:
                                    if not hasattr(msg, 'additional_kwargs') or msg.additional_kwargs is None:
                                        msg.additional_kwargs = {}
                                    if 'reasoning_content' not in msg.additional_kwargs:
                                        reasoning = msg.content if hasattr(msg, 'content') and msg.content else ""
                                        if not reasoning or reasoning.strip() == "":
                                            reasoning = "正在思考如何使用工具来回答这个问题..."
                                        msg.additional_kwargs['reasoning_content'] = reasoning
                                        logger.info(f"✅ [async-错误修复-消息 {i}] BaseMessage 强制添加 reasoning_content")
                        
                        # Re-process messages after fixing
                        kwargs["messages"] = _add_reasoning_content_to_messages_helper(kwargs["messages"])
                        
                        logger.info(f"✅ [async_chat.completions.create-错误修复] 已修复所有消息的 reasoning_content")
                        return await original_async_chat_create(*args, **kwargs)
                    raise
            
            wrapped_model.async_client.create = wrapped_async_chat_create
            logger.info("✅ 已包装 async_client.create 方法")
        
        # Also wrap stream method if it exists (for streaming)
        if hasattr(wrapped_model.client, 'stream'):
            original_stream = wrapped_model.client.stream
            
            def add_reasoning_to_messages(messages):
                """Helper to add reasoning_content for stream method.
                
                Uses the standalone helper function to ensure consistency across all code paths.
                """
                return _add_reasoning_content_to_messages_helper(messages)
            
            def wrapped_stream(*args, **kwargs):
                """Wrapper for stream method that adds reasoning_content."""
                if "messages" in kwargs:
                    kwargs["messages"] = add_reasoning_to_messages(kwargs["messages"])
                return original_stream(*args, **kwargs)
            
            wrapped_model.client.stream = wrapped_stream
        
        return wrapped_model

