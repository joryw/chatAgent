"""Agent configuration management."""

import json
import os
from typing import Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from ..models.factory import get_model_wrapper
from ..models.base import BaseModelWrapper
from langchain_core.language_models import BaseChatModel


class AgentConfig(BaseModel):
    """Configuration for Agent mode.
    
    Attributes:
        max_iterations: Maximum number of ReAct iterations
        max_execution_time: Maximum execution time in seconds
        verbose: Whether to output detailed logs
        enable_cache: Whether to enable search result caching
        function_call_model_config: Optional model config JSON string for function calling LLM
        answer_model_config: Optional model config JSON string for answer generation LLM
    """
    
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=10,
        description="Maximum number of ReAct iterations"
    )
    
    max_execution_time: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Maximum execution time in seconds"
    )
    
    verbose: bool = Field(
        default=True,
        description="Whether to output detailed logs"
    )
    
    enable_cache: bool = Field(
        default=True,
        description="Whether to enable search result caching"
    )
    
    function_call_model_config: Optional[str] = Field(
        default=None,
        description="JSON string for function call model configuration (provider, model_name, etc.)"
    )
    
    answer_model_config: Optional[str] = Field(
        default=None,
        description="JSON string for answer generation model configuration (provider, model_name, etc.)"
    )
    
    @field_validator("max_iterations")
    @classmethod
    def validate_max_iterations(cls, v: int) -> int:
        """Validate max_iterations is within reasonable bounds."""
        if v < 1:
            raise ValueError("max_iterations must be at least 1")
        if v > 10:
            raise ValueError("max_iterations must be at most 10 to control costs")
        return v
    
    @field_validator("max_execution_time")
    @classmethod
    def validate_max_execution_time(cls, v: int) -> int:
        """Validate max_execution_time is within reasonable bounds."""
        if v < 10:
            raise ValueError("max_execution_time must be at least 10 seconds")
        if v > 300:
            raise ValueError("max_execution_time must be at most 300 seconds (5 minutes)")
        return v
    
    @field_validator("function_call_model_config", "answer_model_config")
    @classmethod
    def validate_model_config_json(cls, v: Optional[str]) -> Optional[str]:
        """Validate model config JSON string is valid."""
        if v is None:
            return v
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in model config: {e}")
        return v
    
    class Config:
        """Pydantic config."""
        env_prefix = "AGENT_"


def get_agent_config() -> AgentConfig:
    """Get Agent configuration from environment variables.
    
    Returns:
        AgentConfig instance with values from environment or defaults
    
    Environment Variables:
        AGENT_MAX_ITERATIONS: Maximum number of iterations (default: 5)
        AGENT_MAX_EXECUTION_TIME: Maximum execution time in seconds (default: 60)
        AGENT_VERBOSE: Whether to output detailed logs (default: true)
        AGENT_ENABLE_CACHE: Whether to enable search result caching (default: true)
        AGENT_FUNCTION_CALL_MODEL: JSON string for function call model config (optional)
        AGENT_ANSWER_MODEL: JSON string for answer generation model config (optional)
    """
    return AgentConfig(
        max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
        max_execution_time=int(os.getenv("AGENT_MAX_EXECUTION_TIME", "60")),
        verbose=os.getenv("AGENT_VERBOSE", "true").lower() == "true",
        enable_cache=os.getenv("AGENT_ENABLE_CACHE", "true").lower() == "true",
        function_call_model_config=os.getenv("AGENT_FUNCTION_CALL_MODEL"),
        answer_model_config=os.getenv("AGENT_ANSWER_MODEL"),
    )


def get_default_mode() -> str:
    """Get default conversation mode from environment.
    
    Returns:
        'chat' or 'agent', defaults to 'agent'
    """
    mode = os.getenv("DEFAULT_MODE", "agent").lower()
    if mode not in ["chat", "agent"]:
        return "agent"
    return mode


def parse_model_config_from_json(config_json: Optional[str]) -> Optional[dict]:
    """Parse model configuration from JSON string.
    
    Args:
        config_json: JSON string containing model configuration
        
    Returns:
        Dictionary with model configuration or None if config_json is None
        
    Raises:
        ValueError: If JSON is invalid
    """
    if config_json is None:
        return None
    
    try:
        config_dict = json.loads(config_json)
        return config_dict
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in model config: {e}")


def create_agent_llms_from_config(
    default_provider: str,
    agent_config: Optional[AgentConfig] = None
) -> Tuple[BaseChatModel, Optional[BaseChatModel]]:
    """Create LLM instances for Agent from configuration.
    
    Args:
        default_provider: Default provider to use if not specified in config
        agent_config: Agent configuration (optional, loads from env if None)
        
    Returns:
        Tuple of (function_call_llm, answer_llm)
        If answer_llm config is not provided, returns None for answer_llm
    """
    if agent_config is None:
        agent_config = get_agent_config()
    
    # Create function_call_llm
    function_call_config_json = agent_config.function_call_model_config
    if function_call_config_json:
        config_dict = parse_model_config_from_json(function_call_config_json)
        provider_str = config_dict.get("provider", default_provider)
        # Use get_model_config to create proper config
        from .model_config import get_model_config
        function_call_config = get_model_config(provider=provider_str)
        # Override with values from JSON if provided
        if "model_name" in config_dict:
            function_call_config.model_name = config_dict["model_name"]
        if "temperature" in config_dict:
            function_call_config.temperature = config_dict["temperature"]
        if "max_tokens" in config_dict:
            function_call_config.max_tokens = config_dict["max_tokens"]
        function_call_wrapper = get_model_wrapper(config=function_call_config)
    else:
        # Use default provider
        function_call_wrapper = get_model_wrapper(provider=default_provider)
    
    function_call_llm = function_call_wrapper.get_langchain_llm()
    
    # Create answer_llm if configured
    answer_llm = None
    answer_config_json = agent_config.answer_model_config
    if answer_config_json:
        config_dict = parse_model_config_from_json(answer_config_json)
        provider_str = config_dict.get("provider", default_provider)
        # Use get_model_config to create proper config
        from .model_config import get_model_config
        answer_config = get_model_config(provider=provider_str)
        # Override with values from JSON if provided
        if "model_name" in config_dict:
            answer_config.model_name = config_dict["model_name"]
        if "temperature" in config_dict:
            answer_config.temperature = config_dict["temperature"]
        if "max_tokens" in config_dict:
            answer_config.max_tokens = config_dict["max_tokens"]
        answer_wrapper = get_model_wrapper(config=answer_config)
        answer_llm = answer_wrapper.get_langchain_llm()
    
    return function_call_llm, answer_llm

