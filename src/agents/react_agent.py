"""ReAct Agent implementation using LangChain."""

import asyncio
import logging
import time
from typing import Optional, AsyncIterator, Any, List

from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from datetime import datetime

from src.agents.base import (
    BaseAgent,
    AgentStep,
    AgentResult,
    AgentTimeoutError,
    AgentIterationLimitError,
    AgentExecutionError,
)
from src.agents.tools.search_tool import SearchTool
from src.config.agent_config import AgentConfig
from src.config.langsmith_config import get_langsmith_tracer
from src.search.global_citation_manager import GlobalCitationManager

logger = logging.getLogger(__name__)


# ReAct Prompt Template (中文版)
REACT_PROMPT_TEMPLATE = """你是一个有用的 AI 助手，可以使用工具来帮助回答用户的问题。

你有权访问以下工具:

{tools}

使用以下格式进行推理和行动:

Question: 用户的输入问题
Thought: 你应该思考如何回答这个问题
Action: 要使用的工具名称，应该是 [{tool_names}] 之一
Action Input: 工具的输入参数
Observation: 工具返回的结果
... (这个 Thought/Action/Action Input/Observation 可以重复 N 次)
Thought: 我现在知道最终答案了
Final Answer: 对用户问题的最终回答

重要规则:
1. 当需要最新信息或实时数据时，使用 web_search 工具
2. 当工具返回结果后，仔细分析是否足够回答问题
3. 如果信息不足，可以再次使用工具搜索更多信息
4. 在最终回答中，使用 [数字] 格式引用搜索结果的来源
5. 最终回答应该准确、完整、有引用

开始!

Question: {input}
Thought: {agent_scratchpad}
"""


def add_date_to_messages(messages):
    """Add date information to system messages.
    
    Args:
        messages: List of messages (can be list or single message)
        
    Returns:
        Modified list of messages with date information
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    date_info = f"当前日期：{current_date}"
    
    # Handle both list and single message
    if not isinstance(messages, list):
        messages = [messages]
    
    # Check if there's already a system message
    has_system = False
    modified_messages = []
    
    for msg in messages:
        if isinstance(msg, SystemMessage):
            # Append date info to existing system message
            modified_messages.append(
                SystemMessage(content=f"{msg.content}\n\n{date_info}")
            )
            has_system = True
        else:
            modified_messages.append(msg)
    
    # If no system message, add one with date info
    if not has_system:
        modified_messages.insert(0, SystemMessage(content=date_info))
    
    return modified_messages


class StreamingCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming Agent steps."""
    
    def __init__(self, step_queue: asyncio.Queue):
        """Initialize callback handler.
        
        Args:
            step_queue: Queue to put AgentStep objects
        """
        self.step_queue = step_queue
        self.current_reasoning = ""
    
    async def on_agent_action(
        self, action: AgentAction, **kwargs: Any
    ) -> None:
        """Called when agent takes an action.
        
        Args:
            action: AgentAction object
        """
        # Send reasoning step if we have accumulated text
        if self.current_reasoning:
            await self.step_queue.put(
                AgentStep(
                    type="reasoning",
                    content=self.current_reasoning.strip(),
                )
            )
            self.current_reasoning = ""
        
        # Send action step
        await self.step_queue.put(
            AgentStep(
                type="action",
                content=f"使用工具: {action.tool}",
                metadata={
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                }
            )
        )
    
    async def on_agent_finish(
        self, finish: AgentFinish, **kwargs: Any
    ) -> None:
        """Called when agent finishes.
        
        Args:
            finish: AgentFinish object
        """
        # Send final reasoning if any
        if self.current_reasoning:
            await self.step_queue.put(
                AgentStep(
                    type="reasoning",
                    content=self.current_reasoning.strip(),
                )
            )
        
        # Send final answer
        await self.step_queue.put(
            AgentStep(
                type="final",
                content=finish.return_values.get("output", ""),
            )
        )
    
    async def on_tool_start(
        self, serialized: dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when tool starts.
        
        Args:
            serialized: Tool serialization
            input_str: Tool input string
        """
        tool_name = serialized.get("name", "unknown")
        logger.info(f"🔧 工具开始: {tool_name}, 输入: {input_str}")
    
    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when tool ends.
        
        Args:
            output: Tool output string
        """
        # Send observation step
        await self.step_queue.put(
            AgentStep(
                type="observation",
                content=output,
            )
        )
    
    async def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when tool encounters an error.
        
        Args:
            error: Exception that occurred
        """
        logger.error(f"❌ 工具执行错误: {error}")
        await self.step_queue.put(
            AgentStep(
                type="observation",
                content=f"工具执行失败: {str(error)}",
            )
        )
    
    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token.
        
        Args:
            token: New token string
        """
        # Accumulate reasoning tokens
        self.current_reasoning += token


class ReActAgent(BaseAgent):
    """ReAct Agent implementation.
    
    This agent implements the ReAct (Reasoning + Acting) pattern using LangChain.
    It can use tools (like web search) to gather information before answering.
    
    Supports dual LLM architecture:
    - function_call_llm: Used for tool calling decisions
    - answer_llm: Used for generating final answers
    
    Attributes:
        config: Agent configuration
        function_call_llm: Language model for function calling
        answer_llm: Language model for answer generation
        tools: List of available tools
        agent_executor: LangChain AgentExecutor (uses function_call_llm)
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        search_tool: SearchTool,
        config: Optional[AgentConfig] = None,
        answer_llm: Optional[BaseChatModel] = None,
        additional_tools: Optional[List[BaseTool]] = None,
    ):
        """Initialize ReAct Agent.
        
        Args:
            llm: Language model instance for function calling (function_call_llm)
            search_tool: Search tool instance
            config: Agent configuration (optional)
            answer_llm: Optional language model for answer generation.
                       If None, uses llm for both stages (backward compatibility)
            additional_tools: Optional list of additional tools (e.g., MCP tools)
        """
        self.config = config or AgentConfig()
        self.function_call_llm = llm
        # If answer_llm is not provided, use function_call_llm for both stages
        self.answer_llm = answer_llm if answer_llm is not None else llm
        
        # Create global citation manager for Agent mode
        self.citation_manager = GlobalCitationManager()
        
        # Attach citation manager to search tool for global numbering
        search_tool.citation_manager = self.citation_manager
        
        self.tools = [search_tool]
        if additional_tools:
            self.tools.extend(additional_tools)
        
        # CRITICAL: Bind tools to the model for function calling
        # LangGraph's create_react_agent requires the model to have tools bound
        # Some models (like DeepSeek) need explicit tool binding
        try:
            # Try to bind tools if the model supports it
            if hasattr(self.function_call_llm, 'bind_tools'):
                logger.info(f"🔧 绑定 {len(self.tools)} 个工具到模型...")
                bound_llm = self.function_call_llm.bind_tools(self.tools)
            else:
                # If bind_tools is not available, use the model as-is
                # LangGraph's create_react_agent should handle tool binding internally
                logger.debug("模型不支持 bind_tools，使用原始模型")
                bound_llm = self.function_call_llm
        except Exception as e:
            logger.warning(f"⚠️ 工具绑定失败，使用原始模型: {e}")
            bound_llm = self.function_call_llm
        
        # Create ReAct agent using LangGraph with function_call_llm
        # LangGraph's create_react_agent handles prompt creation internally
        # It will automatically bind tools if not already bound
        self.agent_executor = create_react_agent(
            model=bound_llm,
            tools=self.tools,
        )
        
        logger.info(f"✅ Agent executor 创建完成，工具数量: {len(self.tools)}")
        
        # Track if using dual LLM mode
        using_dual_llm = answer_llm is not None
        
        # Log tool information for debugging
        tool_names = [tool.name for tool in self.tools]
        logger.info(
            f"✅ ReAct Agent 初始化完成 "
            f"(max_iterations={self.config.max_iterations}, "
            f"max_execution_time={self.config.max_execution_time}s, "
            f"dual_llm_mode={using_dual_llm}, "
            f"tools={tool_names})"
        )
    
    def _should_generate_answer(self, tool_results: list[str], iteration_count: int) -> bool:
        """Evaluate if tool calling results are sufficient to generate answer.
        
        Args:
            tool_results: List of tool execution results
            iteration_count: Number of tool calling iterations performed
            
        Returns:
            True if should generate answer, False if should continue tool calling
        """
        # Stop if reached max iterations
        if iteration_count >= self.config.max_iterations:
            logger.info(f"达到最大迭代次数 ({self.config.max_iterations})，停止工具调用")
            return True
        
        # Stop if we have results and they're not empty
        if tool_results:
            # Check if any result has meaningful content (more than 50 chars)
            meaningful_results = [r for r in tool_results if len(r.strip()) > 50]
            if meaningful_results:
                logger.info(f"工具调用结果充足 ({len(meaningful_results)} 条有效结果)，准备生成回答")
                return True
        
        # Continue tool calling
        return False
    
    async def _generate_answer_with_answer_llm_streaming(
        self, 
        user_input: str, 
        tool_results: list[str],
        tool_calls: list[dict]
    ):
        """Generate final answer using answer_llm with streaming support.
        
        This method yields AgentStep objects for reasoning and answer content.
        
        Args:
            user_input: Original user question
            tool_results: List of tool execution results
            tool_calls: List of tool call information
            
        Yields:
            AgentStep objects for reasoning and answer content
        """
        # Build context from tool results
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if tool_results:
            # Has tool results - generate answer based on them
            context_parts = []
            for i, result in enumerate(tool_results, 1):
                context_parts.append(f"[搜索结果 {i}]\n{result}")
            
            context = "\n\n".join(context_parts)
            
            system_prompt = f"""你是一个有用的 AI 助手。基于以下搜索结果，为用户的问题提供一个准确、完整、有引用的回答。

当前日期：{current_date}

重要规则:
1. 仔细分析搜索结果，提取相关信息
2. 在回答中使用 [数字] 格式引用搜索结果来源
3. 如果搜索结果不足以回答问题，如实说明
4. 回答应该准确、完整、有条理
5. 如果用户询问日期或时间相关问题，请使用上述当前日期信息回答
"""
            
            user_prompt = f"""用户问题: {user_input}

搜索结果:
{context}

请基于以上搜索结果回答用户的问题。"""
        else:
            # No tool results - answer directly from model knowledge
            system_prompt = f"""你是一个有用的 AI 助手。请基于你的知识直接回答用户的问题。

当前日期：{current_date}

重要规则:
1. 提供准确、完整、有条理的回答
2. 如果不确定答案，请如实说明
3. 如果用户询问日期或时间相关问题，请使用上述当前日期信息回答
4. 注意：由于达到最大迭代次数限制，未能收集到搜索结果，请基于你的知识直接回答
"""
            
            user_prompt = f"""用户问题: {user_input}

请基于你的知识回答用户的问题。"""
        
        # Generate answer using answer_llm with streaming
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        logger.info(f"使用 answer_llm 流式生成最终回答...")
        
        # Variables to collect full answer for citation processing
        full_answer_content = ""
        reasoning_content = ""
        reasoning_sent = False
        
        # Import citation utilities
        citation_processor = None
        if self.citation_manager:
            from src.search.citation_processor import CitationProcessor
            from src.search.models import SearchResponse
            
            # Create a CitationProcessor with the global citation map
            citation_processor = CitationProcessor(
                SearchResponse(query="", results=[], total_results=0, search_time=0.0), 
                offset=0
            )
            citation_processor.citation_map = self.citation_manager.get_global_citation_map()
        
        # Stream the response with error handling
        try:
            async for chunk in self.answer_llm.astream(messages):
                # Check for reasoning_content (DeepSeek-R1 and similar models)
                if hasattr(chunk, 'additional_kwargs'):
                    deepseek_reasoning = chunk.additional_kwargs.get('reasoning_content')
                    if deepseek_reasoning and not reasoning_sent:
                        reasoning_content = deepseek_reasoning
                        reasoning_sent = True
                        logger.info(f"🧠 Answer LLM 推理过程，长度: {len(reasoning_content)}")
                        yield AgentStep(
                            type="reasoning",
                            content=reasoning_content,
                            metadata={
                                "reasoning_type": "answer_phase",
                                "is_deepseek_reasoning": True,
                                "model": "answer_llm"
                            }
                        )
                
                # Handle regular content
                if hasattr(chunk, 'content') and chunk.content:
                    token = chunk.content
                    full_answer_content += token
                    
                    # Stream tokens directly - we'll convert citations after streaming completes
                    # Real-time conversion is complex due to token boundaries
                    yield AgentStep(
                        type="final",
                        content=token,
                    )
            
            # After streaming completes, convert citations and send updated content
            if citation_processor and full_answer_content:
                # Convert inline citations [1] -> [[1]](url)
                converted_answer = citation_processor.convert_citations(full_answer_content)
                
                # Extract which citations were actually used
                cited_nums = citation_processor._extract_citations(full_answer_content)
                
                # Send a special step to tell UI to replace content with converted version
                logger.info(f"🔗 转换引用链接，共 {len(cited_nums)} 个引用")
                yield AgentStep(
                    type="citation_update",
                    content=converted_answer,
                    metadata={"replace_content": True}
                )
                
                # Add citations list
                if cited_nums:
                    citations_list = self.citation_manager.generate_citations_list(list(cited_nums))
                    logger.info(f"✅ 添加引用列表，包含 {len(cited_nums)} 条引用")
                    yield AgentStep(
                        type="final",
                        content=citations_list,
                    )
            
            logger.info("✅ Answer LLM 流式输出完成")
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Check if this is a timeout error
            is_timeout = "timeout" in error_msg.lower() or "timed out" in error_msg.lower()
            
            if is_timeout:
                logger.error(f"⏱️ Answer LLM 流式输出超时: {e}")
                # Don't yield error here, let the caller handle it with fallback
                raise
            else:
                logger.error(f"❌ Answer LLM 流式输出失败 ({error_type}): {e}", exc_info=True)
                # For other errors, raise to trigger fallback
                raise
    
    def _convert_citation_token(
        self, 
        token: str, 
        full_content: str,
        citation_processor
    ) -> str:
        """Convert citation patterns in a token to clickable links in real-time.
        
        This method detects [num] patterns and converts them to Markdown links.
        Since tokens come one by one, we need to handle partial patterns carefully.
        
        Strategy:
        - We buffer tokens and detect when a complete [num] pattern is formed
        - When detected, we append the URL in Markdown format: [num](url)
        - The UI will render this as a clickable link
        
        Args:
            token: Current token being streamed
            full_content: Full content accumulated so far
            citation_processor: CitationProcessor instance with citation map
            
        Returns:
            Converted token (may be original if no complete pattern found)
        """
        import re
        
        # Only process if token contains [ or ] or digits
        if not any(c in token for c in ['[', ']', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
            return token
        
        # Check the last few characters of full_content for complete [num] patterns
        # Look back up to 15 characters to catch patterns like [123]
        lookback = min(15, len(full_content))
        recent_content = full_content[-lookback:] if lookback > 0 else ""
        
        # Find all complete citation patterns [num]
        pattern = r'\[(\d+)\]'
        matches = list(re.finditer(pattern, recent_content))
        
        if not matches:
            return token
        
        # Check if any match ends at the current position (just completed)
        last_match = matches[-1]
        match_end_in_full = len(full_content) - lookback + last_match.end()
        
        # If the match just completed (ends at current position)
        if match_end_in_full == len(full_content):
            citation_num = int(last_match.group(1))
            citation_info = citation_processor.citation_map.get(citation_num)
            
            if citation_info:
                # Get the URL from citation info
                url = citation_info.get('url', '')
                
                # Calculate the pattern string
                pattern_str = f"[{citation_num}]"
                
                # If entire pattern is in current token (e.g., token is "[1]")
                if pattern_str in token:
                    # Replace the entire pattern with markdown link
                    return token.replace(pattern_str, f"[{citation_num}]({url})")
                
                # More likely: the pattern spans multiple tokens
                # Current token is probably just ']'
                if token.endswith(']'):
                    # We need to append the URL part: (url)
                    # The UI will combine previous tokens [num] with this to form [num](url)
                    return token + f"({url})"
                
                logger.debug(f"引用模式检测到但无法转换: token='{token}', pattern='{pattern_str}'")
            else:
                logger.warning(f"引用编号 {citation_num} 在 citation_map 中未找到")
        
        return token
    
    async def _generate_answer_with_answer_llm(
        self, 
        user_input: str, 
        tool_results: list[str],
        tool_calls: list[dict]
    ) -> str:
        """Generate final answer using answer_llm (non-streaming fallback).
        
        This method uses ainvoke (non-streaming) instead of astream, 
        making it a true fallback when streaming fails or times out.
        
        Args:
            user_input: Original user question
            tool_results: List of tool execution results
            tool_calls: List of tool call information
            
        Returns:
            Generated final answer
        """
        logger.info("尝试使用回退方法...")
        
        # Build context from tool results
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if tool_results:
            context = "\n\n".join(tool_results)
            
            system_prompt = f"""你是一个有用的 AI 助手。基于以下搜索结果，为用户的问题提供一个准确、完整、有引用的回答。

当前日期：{current_date}

重要规则:
1. 仔细分析搜索结果，提取相关信息
2. 在回答中使用 [数字] 格式引用搜索结果来源
3. 如果搜索结果不足以回答问题，如实说明
4. 回答应该准确、完整、有条理
5. 如果用户询问日期或时间相关问题，请使用上述当前日期信息回答
"""
            
            user_prompt = f"""用户问题: {user_input}

搜索结果:
{context}

请基于以上搜索结果回答用户的问题。"""
        else:
            system_prompt = f"""你是一个有用的 AI 助手。请基于你的知识直接回答用户的问题。

当前日期：{current_date}

重要规则:
1. 提供准确、完整、有条理的回答
2. 如果不确定答案，请如实说明
3. 如果用户询问日期或时间相关问题，请使用上述当前日期信息回答
"""
            
            user_prompt = f"""用户问题: {user_input}

请基于你的知识回答用户的问题。"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            # Use ainvoke (non-streaming) with increased timeout
            response = await self.answer_llm.ainvoke(messages)
            full_answer = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"✅ 回退方法成功，回答长度: {len(full_answer)}")
            return full_answer
            
        except Exception as e:
            logger.error(f"❌ 回退方法失败: {e}")
            # Return a basic error message
            return "抱歉，由于网络原因，无法生成完整的回答。请稍后重试。"
    
    async def run(self, user_input: str) -> AgentResult:
        """Run agent on user input.
        
        Args:
            user_input: User's question
            
        Returns:
            AgentResult with final answer and steps
            
        Raises:
            AgentTimeoutError: If execution exceeds time limit
            AgentExecutionError: If execution fails
        """
        logger.info(f"🤖 Agent 开始执行: {user_input}")
        start_time = time.time()
        
        # Reset citation manager for new conversation
        self.citation_manager.reset()
        
        # Check if using dual LLM mode
        using_dual_llm = self.answer_llm is not self.function_call_llm
        
        try:
            # Get LangSmith tracer if enabled
            tracer = get_langsmith_tracer()
            callbacks = [tracer] if tracer else None
            
            # Run agent with timeout using LangGraph API
            # LangGraph expects messages, not a dict with "input" key
            # Add date information to the input message
            user_msg = HumanMessage(content=user_input)
            # Create a system message with date info for the agent
            current_date = datetime.now().strftime("%Y-%m-%d")
            date_msg = SystemMessage(content=f"当前日期：{current_date}\n\n重要提示：如果用户询问日期或时间相关问题，请直接使用上述当前日期信息回答，无需使用搜索工具。")
            invoke_input = {"messages": [date_msg, user_msg]}
            
            # Prepare config with callbacks and recursion limit
            # LangGraph uses recursion_limit to control max iterations
            invoke_config = {
                "recursion_limit": self.config.max_iterations,
            }
            if callbacks:
                invoke_config["callbacks"] = callbacks
            
            result = await asyncio.wait_for(
                self.agent_executor.ainvoke(invoke_input, config=invoke_config),
                timeout=self.config.max_execution_time,
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Agent 工具调用阶段完成，耗时 {elapsed_time:.2f}s")
            
            # LangGraph result contains messages
            messages = result.get("messages", [])
            
            # Extract tool results and tool calls
            tool_results = []
            tool_calls = []
            steps = []
            iteration_count = 0
            
            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        iteration_count += 1
                        for tool_call in msg.tool_calls:
                            tool_calls.append({
                                "name": tool_call.get("name"),
                                "args": tool_call.get("args"),
                            })
                            steps.append(
                                AgentStep(
                                    type="action",
                                    content=f"使用工具: {tool_call.get('name', 'unknown')}",
                                    metadata={
                                        "tool": tool_call.get("name"),
                                        "tool_input": tool_call.get("args"),
                                    }
                                )
                            )
                    elif msg.content:
                        # This might be reasoning or final answer from function_call_llm
                        if not using_dual_llm:
                            # Single LLM mode: use this as final answer
                            steps.append(
                                AgentStep(
                                    type="final",
                                    content=msg.content,
                                )
                            )
                elif hasattr(msg, "content") and str(msg.content):
                    # Tool message (observation)
                    tool_results.append(str(msg.content))
                    steps.append(
                        AgentStep(
                            type="observation",
                            content=str(msg.content),
                        )
                    )
            
            # Generate final answer
            if using_dual_llm:
                # Dual LLM mode: use answer_llm to generate final answer
                logger.info("🔄 切换到 answer_llm 生成最终回答...")
                final_answer = await self._generate_answer_with_answer_llm(
                    user_input, tool_results, tool_calls
                )
                steps.append(
                    AgentStep(
                        type="final",
                        content=final_answer,
                    )
                )
            else:
                # Single LLM mode: use the answer from agent_executor
                final_message = messages[-1] if messages else None
                final_answer = final_message.content if final_message else ""
                if not final_answer:
                    # Fallback: generate answer if agent didn't produce one
                    logger.warning("⚠️ Agent 未生成最终回答，使用 answer_llm 生成...")
                    final_answer = await self._generate_answer_with_answer_llm(
                        user_input, tool_results, tool_calls
                    )
                    steps.append(
                        AgentStep(
                            type="final",
                            content=final_answer,
                        )
                    )
            
            total_time = time.time() - start_time
            logger.info(f"✅ Agent 执行完成，总耗时 {total_time:.2f}s")
            
            return AgentResult(
                final_answer=final_answer,
                steps=steps,
                total_iterations=iteration_count,
            )
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            logger.error(f"⏱️ Agent 执行超时 ({elapsed_time:.2f}s)")
            raise AgentTimeoutError(
                f"Agent 执行超时 ({self.config.max_execution_time}秒)。"
                f"请尝试简化问题或切换到 Chat 模式。"
            )
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"❌ Agent 执行失败 ({elapsed_time:.2f}s): {e}")
            
            # Check if this is a recursion limit error
            is_recursion_limit = "recursion_limit" in error_msg.lower() or "GRAPH_RECURSION_LIMIT" in error_msg
            
            if is_recursion_limit:
                # For recursion limit errors in run method, we can't extract partial results
                # because ainvoke throws exception before we can process results
                # Suggest user to use stream method or increase limit
                raise AgentIterationLimitError(
                    f"达到最大迭代次数 ({self.config.max_iterations})。"
                    f"请尝试：\n"
                    f"1. 简化您的问题\n"
                    f"2. 增加最大迭代次数（设置环境变量 AGENT_MAX_ITERATIONS，范围 1-10）\n"
                    f"3. 使用流式模式可能会在达到限制时基于已有结果生成答案"
                )
            else:
                raise AgentExecutionError(f"Agent 执行失败: {str(e)}")
    
    async def stream(self, user_input: str) -> AsyncIterator[AgentStep]:
        """Stream agent execution steps.
        
        Args:
            user_input: User's question
            
        Yields:
            AgentStep objects as they are generated
            
        Raises:
            AgentTimeoutError: If execution exceeds time limit
        """
        logger.info(f"🤖 Agent 开始流式执行: {user_input}")
        
        # Check if using dual LLM mode
        using_dual_llm = self.answer_llm is not self.function_call_llm
        
        try:
            # Try streaming first
            has_yielded = False
            all_messages = []
            tool_results = []
            tool_calls = []
            final_answer_from_function_call = None
            
            # Get LangSmith tracer if enabled
            tracer = get_langsmith_tracer()
            callbacks = [tracer] if tracer else None
            
            # Stream events from LangGraph
            # Add date information to the input message
            user_msg = HumanMessage(content=user_input)
            current_date = datetime.now().strftime("%Y-%m-%d")
            date_msg = SystemMessage(content=f"当前日期：{current_date}\n\n重要提示：如果用户询问日期或时间相关问题，请直接使用上述当前日期信息回答，无需使用搜索工具。")
            stream_input = {"messages": [date_msg, user_msg]}
            
            # Prepare config with callbacks and recursion limit
            # LangGraph uses recursion_limit to control max iterations
            stream_config = {
                "recursion_limit": self.config.max_iterations,
            }
            if callbacks:
                stream_config["callbacks"] = callbacks
            
            event_stream = self.agent_executor.astream(stream_input, config=stream_config)
            
            # Track the last observation to detect reasoning after observation
            last_observation_time = None
            pending_reasoning_after_observation = False
            
            async for event in event_stream:
                has_yielded = True
                # LangGraph returns events with node names as keys
                # e.g., {"agent": {...}, "tools": {...}}
                event_keys = list(event.keys())
                logger.debug(f"收到事件: {event_keys}")
                
                # Log if we're receiving agent events but no tool calls
                if "agent" in event and "tools" not in event_keys:
                    logger.debug(f"🔍 Agent 节点事件，检查是否包含工具调用...")
                
                # Check for agent node (thinking/reasoning)
                if "agent" in event:
                    agent_data = event["agent"]
                    if isinstance(agent_data, dict) and "messages" in agent_data:
                        messages = agent_data["messages"]
                        all_messages.extend(messages)
                        
                        # Check for reasoning and tool calls in AI messages
                        for msg in messages:
                            if isinstance(msg, AIMessage):
                                # First, check for DeepSeek reasoning_content (if available)
                                deepseek_reasoning = None
                                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                                    deepseek_reasoning = msg.additional_kwargs.get("reasoning_content")
                                
                                # Then check for regular content (thinking process)
                                content = msg.content
                                has_reasoning = content and content.strip()
                                
                                # Check for tool_calls in multiple possible locations
                                msg_tool_calls = None
                                if hasattr(msg, "tool_calls") and msg.tool_calls:
                                    msg_tool_calls = msg.tool_calls
                                elif hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                                    msg_tool_calls = msg.additional_kwargs.get("tool_calls")
                                
                                # Determine reasoning type based on context
                                # Key logic:
                                # 1. If has tool_calls -> reasoning before tool call (tool_selection)
                                # 2. If no tool_calls and no observation -> final answer (don't show as reasoning)
                                reasoning_type = None
                                
                                if msg_tool_calls:
                                    # Has tool calls -> this is reasoning before tool selection
                                    reasoning_type = "tool_selection"
                                elif last_observation_time is not None:
                                    # Just received observation but no tool calls - reset tracking
                                    # Don't show this as a reasoning step (user doesn't need to see "thinking about continuing")
                                    pending_reasoning_after_observation = False
                                    last_observation_time = None
                                    reasoning_type = None
                                elif not using_dual_llm and has_reasoning:
                                    # Single LLM mode, no tool calls, has content -> this is final answer, not reasoning
                                    # Don't show as reasoning step
                                    reasoning_type = None
                                
                                # Show DeepSeek reasoning_content if available (always show this as it's internal thinking)
                                if deepseek_reasoning and deepseek_reasoning.strip():
                                    logger.info(f"🧠 DeepSeek 内部思考过程，长度: {len(deepseek_reasoning)}")
                                    yield AgentStep(
                                        type="reasoning",
                                        content=deepseek_reasoning.strip(),
                                        metadata={
                                            "reasoning_type": "deepseek_internal",
                                            "is_deepseek_reasoning": True,
                                        }
                                    )
                                
                                # Only show regular reasoning if we determined it's actually reasoning (not final answer)
                                # Skip if it's the same as deepseek_reasoning to avoid duplication
                                if has_reasoning and reasoning_type is not None:
                                    reasoning_content = content.strip()
                                    
                                    # Skip if this content is the same as deepseek_reasoning (avoid duplication)
                                    if deepseek_reasoning and reasoning_content == deepseek_reasoning.strip():
                                        logger.debug("跳过重复的 reasoning content（与 DeepSeek reasoning_content 相同）")
                                    else:
                                        # Only show tool_selection reasoning (before using a tool)
                                        if reasoning_type == "tool_selection":
                                            logger.info(f"💭 Agent 思考选择工具，长度: {len(reasoning_content)}")
                                            yield AgentStep(
                                                type="reasoning",
                                                content=reasoning_content,
                                                metadata={
                                                    "reasoning_type": reasoning_type,
                                                }
                                            )
                                
                                # Then send tool calls if present
                                if msg_tool_calls:
                                    # This is a tool call decision (after reasoning about tool selection)
                                    logger.info(f"🔧 Agent 决定调用工具，工具调用数量: {len(msg_tool_calls)}")
                                    for tool_call in msg_tool_calls:
                                        # Handle different tool_call formats
                                        if isinstance(tool_call, dict):
                                            tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name", "unknown")
                                            tool_input = tool_call.get("args") or tool_call.get("function", {}).get("arguments", {})
                                        else:
                                            # Handle object format
                                            tool_name = getattr(tool_call, "name", "unknown")
                                            tool_input = getattr(tool_call, "args", {})
                                        
                                        tool_calls.append({
                                            "name": tool_name,
                                            "args": tool_input,
                                        })
                                        logger.info(f"🔧 Agent 决定调用工具: {tool_name}, 输入: {tool_input}")
                                        yield AgentStep(
                                            type="action",
                                            content=f"调用工具: {tool_name}",
                                            metadata={
                                                "tool": tool_name,
                                                "tool_input": str(tool_input),
                                            }
                                        )
                                    # Reset observation tracking after tool call decision
                                    last_observation_time = None
                                elif not has_reasoning and not using_dual_llm:
                                    # No tool calls, no reasoning, and single LLM mode - might be final answer
                                    # Store for later use if this is the final message
                                    if content and len(all_messages) > 1:
                                        final_answer_from_function_call = content
                                    # Reset observation tracking
                                    last_observation_time = None
                                elif has_reasoning and reasoning_type is None:
                                    # This is final answer in single LLM mode, store it
                                    if not using_dual_llm and len(all_messages) > 1:
                                        final_answer_from_function_call = content
                                    # Reset observation tracking
                                    last_observation_time = None
                
                # Check for tools node (tool execution results)
                elif "tools" in event:
                    tools_data = event["tools"]
                    if isinstance(tools_data, dict) and "messages" in tools_data:
                        tool_messages = tools_data["messages"]
                        all_messages.extend(tool_messages)
                        
                        # Extract tool output
                        for msg in tool_messages:
                            if hasattr(msg, "content"):
                                tool_output = str(msg.content)
                                tool_results.append(tool_output)
                                logger.info(f"✅ 工具执行完成，结果长度: {len(tool_output)}")
                                yield AgentStep(
                                    type="observation",
                                    content=tool_output[:500] + "..." if len(tool_output) > 500 else tool_output,
                                )
                                # Mark that we just received an observation - next reasoning will be about continuing
                                last_observation_time = time.time()
                                pending_reasoning_after_observation = True
            
            # Generate final answer
            if using_dual_llm:
                # Dual LLM mode: use answer_llm to generate final answer
                logger.info("🔄 切换到 answer_llm 生成最终回答...")
                yield AgentStep(
                    type="reasoning",
                    content="正在使用 answer_llm 生成最终回答...",
                )
                
                # Use the new streaming method with reasoning support
                try:
                    async for answer_step in self._generate_answer_with_answer_llm_streaming(
                        user_input, tool_results, tool_calls
                    ):
                        yield answer_step
                    
                    # 双 LLM 模式答案生成完成，终止流式输出
                    logger.info("✅ 双 LLM 模式流式输出完成")
                    return
                    
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    is_timeout = "timeout" in error_msg.lower() or "timed out" in error_msg.lower()
                    
                    if is_timeout:
                        logger.warning(f"⏱️ Answer LLM 流式输出超时，尝试使用回退方法...")
                    else:
                        logger.warning(f"⚠️ Answer LLM 流式输出失败 ({type(stream_error).__name__})，尝试使用回退方法...")
                    
                    # Try fallback method (non-streaming)
                    try:
                        answer = await self._generate_answer_with_answer_llm(
                            user_input, tool_results, tool_calls
                        )
                        
                        # Process citations if available
                        if self.citation_manager and tool_results:
                            from src.search.citation_processor import CitationProcessor
                            from src.search.models import SearchResponse
                            
                            citation_processor = CitationProcessor(
                                SearchResponse(query="", results=[], total_results=0, search_time=0.0),
                                offset=0
                            )
                            citation_processor.citation_map = self.citation_manager.get_global_citation_map()
                            
                            # Convert citations and get reference list
                            converted_answer = citation_processor.convert_citations(answer)
                            cited_nums = citation_processor._extract_citations(answer)
                            
                            yield AgentStep(
                                type="final",
                                content=converted_answer,
                            )
                            
                            if cited_nums:
                                citations_list = self.citation_manager.generate_citations_list(list(cited_nums))
                                logger.info(f"✅ (回退方法) 添加引用列表，包含 {len(cited_nums)} 条引用")
                                yield AgentStep(
                                    type="final",
                                    content=citations_list,
                                )
                        else:
                            yield AgentStep(
                                type="final",
                                content=answer,
                            )
                        
                        logger.info("✅ 回退方法成功完成")
                        return
                        
                    except Exception as fallback_error:
                        logger.error(f"❌ 回退方法也失败: {fallback_error}", exc_info=True)
                        yield AgentStep(
                            type="error",
                            content="抱歉，由于网络原因，无法生成完整的回答。请稍后重试。",
                        )
                        return
            elif not using_dual_llm:
                # Single LLM mode: use answer from function_call_llm
                if not final_answer_from_function_call:
                    # Extract final answer from all messages
                    for msg in reversed(all_messages):
                        if isinstance(msg, AIMessage):
                            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                                final_answer_from_function_call = msg.content
                                break
                
                if final_answer_from_function_call:
                    logger.info("✅ Agent 生成最终答案（单 LLM 模式）")
                    # Process citations if available
                    if self.citation_manager and tool_results:
                        from src.search.citation_processor import CitationProcessor
                        from src.search.models import SearchResponse
                        
                        # Create a CitationProcessor with the global citation map
                        citation_processor = CitationProcessor(
                            SearchResponse(query="", results=[], total_results=0, search_time=0.0), 
                            offset=0
                        )
                        citation_processor.citation_map = self.citation_manager.get_global_citation_map()
                        
                        # Convert inline citations and append reference list
                        converted_answer = citation_processor.convert_citations(final_answer_from_function_call)
                        cited_nums = citation_processor._extract_citations(final_answer_from_function_call)
                        
                        yield AgentStep(
                            type="final",
                            content=converted_answer,
                        )
                        
                        if cited_nums:
                            citations_list = self.citation_manager.generate_citations_list(list(cited_nums))
                            logger.info(f"✅ 添加引用列表（单 LLM 模式），包含 {len(cited_nums)} 条引用")
                            yield AgentStep(
                                type="final",
                                content=citations_list,
                            )
                    else:
                        yield AgentStep(
                            type="final",
                            content=final_answer_from_function_call,
                        )
                    
                    # 单 LLM 模式答案生成完成，终止流式输出
                    logger.info("✅ 单 LLM 模式流式输出完成")
                    return
                elif not has_yielded:
                    # Fallback: if streaming didn't work, use non-streaming method
                    logger.warning("⚠️ 流式输出未返回事件，使用回退方法")
                    yield AgentStep(
                        type="reasoning",
                        content="正在处理请求...",
                    )
                    result = await self.run(user_input)
                    for step in result.steps:
                        yield step
                    logger.info("✅ 回退方法完成")
                    return
                else:
                    # Last resort: generate answer using answer_llm if available
                    logger.warning("⚠️ Agent 未从流式输出中找到最终答案，尝试使用回退方法...")
                    try:
                        # Use the fallback method with real non-streaming API call
                        answer = await self._generate_answer_with_answer_llm(
                            user_input, tool_results, tool_calls
                        )
                        
                        # Process citations if available
                        if self.citation_manager and tool_results:
                            from src.search.citation_processor import CitationProcessor
                            from src.search.models import SearchResponse
                            
                            citation_processor = CitationProcessor(
                                SearchResponse(query="", results=[], total_results=0, search_time=0.0),
                                offset=0
                            )
                            citation_processor.citation_map = self.citation_manager.get_global_citation_map()
                            
                            # Convert citations and get reference list
                            converted_answer = citation_processor.convert_citations(answer)
                            cited_nums = citation_processor._extract_citations(answer)
                            
                            yield AgentStep(
                                type="final",
                                content=converted_answer,
                            )
                            
                            if cited_nums:
                                citations_list = self.citation_manager.generate_citations_list(list(cited_nums))
                                logger.info(f"✅ (回退方法) 添加引用列表，包含 {len(cited_nums)} 条引用")
                                yield AgentStep(
                                    type="final",
                                    content=citations_list,
                                )
                        else:
                            yield AgentStep(
                                type="final",
                                content=answer,
                            )
                        
                        logger.info("✅ 回退方法成功完成")
                        return
                    except Exception as gen_error:
                        logger.error(f"❌ 回退方法也失败: {gen_error}", exc_info=True)
                        yield AgentStep(
                            type="error",
                            content="抱歉，由于网络原因，无法生成完整的回答。请稍后重试。",
                        )
                        return
            
            logger.info("✅ Agent 流式执行完成")
            
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Agent 流式执行超时")
            yield AgentStep(
                type="error",
                content=f"执行超时 ({self.config.max_execution_time}秒)",
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Agent 流式执行失败: {e}", exc_info=True)
            
            # Check if this is a recursion limit error
            is_recursion_limit = (
                "recursion_limit" in error_msg.lower() or 
                "GRAPH_RECURSION_LIMIT" in error_msg or
                "need more steps" in error_msg.lower()
            )
            
            if is_recursion_limit:
                # We hit recursion limit - generate answer from collected results (or without)
                if tool_results:
                    logger.warning(f"⚠️ 达到最大迭代次数 ({self.config.max_iterations})，已收集到 {len(tool_results)} 个工具结果，将基于现有结果生成答案")
                else:
                    logger.warning(f"⚠️ 达到最大迭代次数 ({self.config.max_iterations})，未收集到工具结果，将基于模型知识直接回答问题")
                
                # Always generate answer when hitting recursion limit, regardless of tool_results
                if using_dual_llm:
                    # Use answer_llm to generate final answer
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    
                    if tool_results:
                        # Has tool results - generate answer based on them
                        context = "\n\n".join(tool_results)
                        
                        system_prompt = f"""你是一个有用的 AI 助手。基于以下搜索结果，为用户的问题提供一个准确、完整、有引用的回答。

当前日期：{current_date}

重要规则:
1. 仔细分析搜索结果，提取相关信息
2. 在回答中使用 [数字] 格式引用搜索结果来源
3. 如果搜索结果不足以回答问题，如实说明
4. 回答应该准确、完整、有条理
5. 如果用户询问日期或时间相关问题，请使用上述当前日期信息回答
6. 注意：由于达到最大迭代次数，请基于已有信息给出最佳答案
"""
                        
                        user_prompt = f"""用户问题: {user_input}

搜索结果:
{context}

请基于以上搜索结果回答用户的问题。"""
                    else:
                        # No tool results - answer directly from model knowledge
                        system_prompt = f"""你是一个有用的 AI 助手。请基于你的知识直接回答用户的问题。

当前日期：{current_date}

重要规则:
1. 提供准确、完整、有条理的回答
2. 如果不确定答案，请如实说明
3. 如果用户询问日期或时间相关问题，请使用上述当前日期信息回答
4. 注意：由于达到最大迭代次数限制，未能收集到搜索结果，请基于你的知识直接回答
"""
                        
                        user_prompt = f"""用户问题: {user_input}

请基于你的知识回答用户的问题。"""
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_prompt)
                    ]
                    
                    # Stream answer generation and collect the full answer
                    streamed_answer = ""
                    async for chunk in self.answer_llm.astream(messages):
                        if hasattr(chunk, 'content') and chunk.content:
                            streamed_answer += chunk.content
                            yield AgentStep(
                                type="final",
                                content=chunk.content,
                            )
                    
                    # After streaming is complete, convert citations and add reference list
                    if self.citation_manager and tool_results:
                        from src.search.citation_processor import CitationProcessor
                        from src.search.models import SearchResponse
                        
                        # Create a CitationProcessor with the global citation map
                        citation_processor = CitationProcessor(
                            SearchResponse(query="", results=[], total_results=0, search_time=0.0), 
                            offset=0
                        )
                        citation_processor.citation_map = self.citation_manager.get_global_citation_map()
                        
                        # Convert inline citations [1] -> [[1]](url)
                        converted_answer = citation_processor.convert_citations(streamed_answer)
                        
                        # Extract which citations were actually used
                        cited_nums = citation_processor._extract_citations(streamed_answer)
                        
                        # Send citation update to replace content
                        logger.info(f"🔗 (错误恢复) 转换引用链接，共 {len(cited_nums)} 个引用")
                        yield AgentStep(
                            type="citation_update",
                            content=converted_answer,
                            metadata={"replace_content": True}
                        )
                        
                        # Generate and append the global citations list
                        if cited_nums:
                            citations_list = self.citation_manager.generate_citations_list(list(cited_nums))
                            logger.info(f"✅ (错误恢复) 添加引用列表，包含 {len(cited_nums)} 条引用")
                            yield AgentStep(
                                type="final",
                                content=citations_list,
                            )
                    
                    # Successfully generated answer, exit exception handler
                    return
                else:
                    # Single LLM mode - always generate answer when hitting recursion limit
                    if final_answer_from_function_call:
                        # Use existing answer if available
                        yield AgentStep(
                            type="final",
                            content=final_answer_from_function_call,
                        )
                    else:
                        # Generate answer from tool results or directly from model
                        if tool_results:
                            yield AgentStep(
                                type="reasoning",
                                content="基于已收集的工具结果生成答案...",
                            )
                        else:
                            yield AgentStep(
                                type="reasoning",
                                content="基于模型知识直接生成答案...",
                            )
                        
                        answer = await self._generate_answer_with_answer_llm(
                            user_input, tool_results, tool_calls
                        )
                        yield AgentStep(
                            type="final",
                            content=answer,
                        )
                    
                    # Successfully generated answer, exit exception handler
                    return
            else:
                # Other errors - try fallback method
                try:
                    logger.info("尝试使用回退方法...")
                    yield AgentStep(
                        type="reasoning",
                        content="流式输出遇到问题，使用备用方法处理...",
                    )
                    result = await self.run(user_input)
                    for step in result.steps:
                        yield step
                    yield AgentStep(
                        type="final",
                        content=result.final_answer,
                    )
                    # Successfully generated answer using fallback, exit exception handler
                    return
                except Exception as fallback_error:
                    logger.error(f"回退方法也失败: {fallback_error}")
                    # If fallback also hits recursion limit, handle it
                    if "recursion_limit" in str(fallback_error).lower() and tool_results:
                        logger.warning("回退方法也达到递归限制，使用已收集的结果生成答案")
                        answer = await self._generate_answer_with_answer_llm(
                            user_input, tool_results, tool_calls
                        )
                        yield AgentStep(
                            type="final",
                            content=answer,
                        )
                        # Successfully generated answer, exit exception handler
                        return
                    else:
                        yield AgentStep(
                            type="error",
                            content=f"执行失败: {str(e)}",
                        )
    
    def reset(self) -> None:
        """Reset agent state."""
        logger.info("🔄 重置 Agent 状态")
        # ReAct agent is stateless, nothing to reset
        pass
    
    def _convert_messages_to_steps(self, messages: list) -> list[AgentStep]:
        """Convert LangGraph messages to AgentStep objects.
        
        Args:
            messages: List of messages from LangGraph
            
        Returns:
            List of AgentStep objects
        """
        steps = []
        
        for msg in messages:
            # Skip human messages (user input)
            if isinstance(msg, HumanMessage):
                continue
            
            # AI messages are responses
            if isinstance(msg, AIMessage):
                if msg.tool_calls:
                    # This is a tool call
                    for tool_call in msg.tool_calls:
                        steps.append(
                            AgentStep(
                                type="action",
                                content=f"使用工具: {tool_call.get('name', 'unknown')}",
                                metadata={
                                    "tool": tool_call.get("name"),
                                    "tool_input": tool_call.get("args"),
                                }
                            )
                        )
                else:
                    # Final answer
                    steps.append(
                        AgentStep(
                            type="final",
                            content=msg.content,
                        )
                    )
            
            # Tool messages are observations
            else:
                steps.append(
                    AgentStep(
                        type="observation",
                        content=str(msg.content),
                    )
                )
        
        return steps

