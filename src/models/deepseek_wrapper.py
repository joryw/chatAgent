"""DeepSeek model wrapper implementation."""

import logging
from typing import AsyncIterator, Optional

import tiktoken
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
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional DeepSeek-specific parameters
        
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
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Override config with kwargs if provided
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            
            # Call DeepSeek API with streaming
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

