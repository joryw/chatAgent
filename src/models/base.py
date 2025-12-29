"""Base model wrapper interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional, List

from ..config.model_config import ModelConfig
from ..config.langsmith_config import get_langsmith_tracer


@dataclass
class ModelResponse:
    """Structured response from model invocation.
    
    Attributes:
        content: Generated text content
        model: Model name used for generation
        tokens_used: Number of tokens used (prompt + completion)
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        finish_reason: Reason for completion (e.g., 'stop', 'length')
    """
    
    content: str
    model: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


@dataclass
class StreamChunk:
    """A chunk from streaming response.
    
    Attributes:
        content: Text content in this chunk
        finish_reason: Reason for completion if stream ended
        chunk_type: Type of content ('reasoning' or 'answer')
    """
    
    content: str
    finish_reason: Optional[str] = None
    chunk_type: str = "answer"  # Default to 'answer' for backward compatibility


class BaseModelWrapper(ABC):
    """Abstract base class for model wrappers.
    
    All model wrappers must implement this interface to ensure
    consistent behavior across different providers.
    """
    
    def __init__(self, config: ModelConfig):
        """Initialize the model wrapper.
        
        Args:
            config: Model configuration
        """
        self.config = config
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate a response from the model.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional model-specific parameters
        
        Returns:
            ModelResponse with generated content and metadata
        
        Raises:
            Exception: If model invocation fails
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response from the model.
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message for context
            **kwargs: Additional model-specific parameters
        
        Yields:
            StreamChunk objects containing response text chunks
        
        Raises:
            Exception: If model invocation fails
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def get_langchain_llm(self):
        """Get LangChain compatible LLM instance.
        
        Returns:
            LangChain BaseChatModel instance
        """
        pass
    
    def _get_callbacks(self) -> List:
        """Get callbacks for LangChain model, including LangSmith tracer if enabled.
        
        Returns:
            List of callback handlers (may be empty if LangSmith is disabled)
        """
        tracer = get_langsmith_tracer()
        if tracer:
            return [tracer]
        return []
    
    def validate_context_length(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> tuple[bool, int]:
        """Check if prompt fits within context window.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
        
        Returns:
            Tuple of (is_valid, total_tokens)
        """
        total_text = (system_message or "") + prompt
        total_tokens = self.count_tokens(total_text)
        
        # Rough estimate: leave room for completion
        max_prompt_tokens = self.config.max_tokens * 0.75
        is_valid = total_tokens <= max_prompt_tokens
        
        return is_valid, total_tokens

