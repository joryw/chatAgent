"""OpenAI model wrapper implementation."""

import logging
from typing import AsyncIterator, Optional

import tiktoken
from langchain_openai import ChatOpenAI
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


class OpenAIWrapper(BaseModelWrapper):
    """Wrapper for OpenAI models using LangChain integration."""
    
    def __init__(self, config: ModelConfig):
        """Initialize OpenAI wrapper.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=config.api_key)
        
        # Initialize LangChain model
        self.model = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            openai_api_key=config.api_key,
            request_timeout=config.timeout,
        )
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(config.model_name)
        except KeyError:
            logger.warning(
                f"No tokenizer found for {config.model_name}, "
                "using cl100k_base encoding"
            )
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
        """Generate a response using OpenAI API.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional OpenAI-specific parameters
        
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
            
            # Prepare messages with date information
            messages = []
            system_message_with_date = self.add_date_info_to_system_message(system_message)
            messages.append({"role": "system", "content": system_message_with_date})
            messages.append({"role": "user", "content": prompt})
            
            # Override config with kwargs if provided
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            
            # Call OpenAI API
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
            logger.error(f"OpenAI API call failed: {str(e)}")
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
        """Generate a streaming response using OpenAI API.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional OpenAI-specific parameters
        
        Yields:
            StreamChunk objects containing response text chunks
        
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
            
            # Prepare messages with date information
            messages = []
            system_message_with_date = self.add_date_info_to_system_message(system_message)
            messages.append({"role": "system", "content": system_message_with_date})
            messages.append({"role": "user", "content": prompt})
            
            # Override config with kwargs if provided
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            
            # Call OpenAI API with streaming
            stream = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.config.timeout,
                stream=True,
            )
            
            # Stream response chunks
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield StreamChunk(
                        content=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                    )
        
        except Exception as e:
            logger.error(f"OpenAI streaming call failed: {str(e)}")
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
        """Get LangChain compatible LLM instance with LangSmith tracing support.
        
        Returns:
            LangChain ChatOpenAI instance with callbacks configured
        """
        callbacks = self._get_callbacks()
        if callbacks:
            # Create a new instance with callbacks if LangSmith is enabled
            return ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                openai_api_key=self.config.api_key,
                request_timeout=self.config.timeout,
                callbacks=callbacks,
            )
        return self.model

