"""Factory for creating model wrappers based on provider."""

import logging
from typing import Optional

from ..config.model_config import ModelConfig, ModelProvider, get_model_config
from .base import BaseModelWrapper
from .openai_wrapper import OpenAIWrapper
from .deepseek_wrapper import DeepSeekWrapper
from .anthropic_wrapper import AnthropicWrapper

logger = logging.getLogger(__name__)


def get_model_wrapper(
    provider: Optional[str] = None,
    config: Optional[ModelConfig] = None,
) -> BaseModelWrapper:
    """Get a model wrapper instance for the specified provider.
    
    Args:
        provider: Provider name (openai, anthropic, deepseek).
                 If None, uses DEFAULT_PROVIDER from environment.
        config: Optional ModelConfig. If None, loads from environment.
    
    Returns:
        Model wrapper instance for the specified provider.
    
    Raises:
        ValueError: If provider is not supported.
    """
    # Load config if not provided
    if config is None:
        config = get_model_config(provider)
    
    # Create appropriate wrapper
    if config.provider == ModelProvider.OPENAI:
        logger.debug(f"Creating OpenAI wrapper with model: {config.model_name}")
        return OpenAIWrapper(config)
    
    elif config.provider == ModelProvider.ANTHROPIC:
        logger.debug(f"Creating Anthropic wrapper with model: {config.model_name}")
        return AnthropicWrapper(config)
    
    elif config.provider == ModelProvider.DEEPSEEK:
        logger.debug(f"Creating DeepSeek wrapper with model: {config.model_name}")
        return DeepSeekWrapper(config)
    
    else:
        raise ValueError(
            f"Unsupported provider: {config.provider}. "
            f"Supported providers: {', '.join([p.value for p in ModelProvider])}"
        )

