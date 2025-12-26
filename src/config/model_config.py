"""Model configuration management with support for multiple providers."""

import os
from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

# Load environment variables
load_dotenv()


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"


class ModelConfig(BaseModel):
    """Configuration for a specific model provider.
    
    Attributes:
        provider: The LLM provider (openai, anthropic, deepseek)
        model_name: Name of the model to use
        api_key: API key for authentication
        base_url: Base URL for API (optional, mainly for DeepSeek)
        temperature: Sampling temperature (0.0 to 2.0)
        max_tokens: Maximum tokens to generate
        top_p: Nucleus sampling parameter
        timeout: Request timeout in seconds
    """
    
    provider: ModelProvider
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    timeout: int = Field(default=30, gt=0)
    
    @validator("api_key")
    def validate_api_key(cls, v: str) -> str:
        """Ensure API key is not empty."""
        if not v or v.startswith("sk-your-"):
            raise ValueError(
                "Invalid API key. Please set a valid API key in your .env file."
            )
        return v
    
    @validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        """Ensure temperature is in valid range."""
        if v < 0.0 or v > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @validator("max_tokens")
    def validate_max_tokens(cls, v: int) -> int:
        """Ensure max_tokens is positive."""
        if v <= 0:
            raise ValueError("max_tokens must be greater than 0")
        return v
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
        protected_namespaces = ()  # Allow model_name field without warning


def get_model_config(provider: Optional[str] = None) -> ModelConfig:
    """Get model configuration for a specific provider.
    
    Args:
        provider: Provider name (openai, anthropic, deepseek).
                 If None, uses DEFAULT_PROVIDER from environment.
    
    Returns:
        ModelConfig instance with settings loaded from environment.
    
    Raises:
        ValueError: If provider is not supported or configuration is invalid.
    """
    if provider is None:
        provider = os.getenv("DEFAULT_PROVIDER", "openai")
    
    provider = provider.lower()
    
    if provider == ModelProvider.OPENAI:
        return ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
        )
    
    elif provider == ModelProvider.ANTHROPIC:
        return ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000")),
        )
    
    elif provider == ModelProvider.DEEPSEEK:
        return ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000")),
        )
    
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {', '.join([p.value for p in ModelProvider])}"
        )


def get_available_providers() -> list[str]:
    """Get list of available providers based on configured API keys.
    
    Returns:
        List of provider names that have valid API keys configured.
    """
    available = []
    
    # Check OpenAI
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-your-"):
        available.append(ModelProvider.OPENAI)
    
    # Check Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key and not anthropic_key.startswith("sk-ant-your-"):
        available.append(ModelProvider.ANTHROPIC)
    
    # Check DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    if deepseek_key and not deepseek_key.startswith("sk-your-"):
        available.append(ModelProvider.DEEPSEEK)
    
    return available

