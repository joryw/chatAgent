"""Anthropic model wrapper implementation (optional for MVP)."""

import logging
from typing import AsyncIterator, Optional

from anthropic import Anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..config.model_config import ModelConfig
from .base import BaseModelWrapper, ModelResponse, StreamChunk

logger = logging.getLogger(__name__)


class AnthropicWrapper(BaseModelWrapper):
    """Wrapper for Anthropic Claude models."""
    
    def __init__(self, config: ModelConfig):
        """Initialize Anthropic wrapper.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=config.api_key)
    
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
        """Generate a response using Anthropic API.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional Anthropic-specific parameters
        
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
            
            # Override config with kwargs if provided
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message or "",
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            
            # Extract response
            content = response.content[0].text
            if not content:
                raise ValueError("Model returned empty response")
            
            # Build structured response
            usage = response.usage
            return ModelResponse(
                content=content,
                model=response.model,
                tokens_used=usage.input_tokens + usage.output_tokens,
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                finish_reason=response.stop_reason,
            )
        
        except Exception as e:
            logger.error(f"Anthropic API call failed: {str(e)}")
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
        """Generate a streaming response using Anthropic API.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional Anthropic-specific parameters
        
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
            
            # Override config with kwargs if provided
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            
            # Call Anthropic API with streaming
            with self.client.messages.stream(
                model=self.config.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message or "",
                messages=[
                    {"role": "user", "content": prompt}
                ],
            ) as stream:
                for text in stream.text_stream:
                    yield StreamChunk(content=text)
        
        except Exception as e:
            logger.error(f"Anthropic streaming call failed: {str(e)}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using Anthropic's token counter.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Number of tokens (approximate)
        """
        # Anthropic uses roughly 4 chars per token as approximation
        # For more accurate counting, we'd need to use their API
        return len(text) // 4

