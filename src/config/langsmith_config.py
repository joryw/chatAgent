"""LangSmith monitoring configuration management."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LangSmithConfig(BaseModel):
    """Configuration for LangSmith monitoring.
    
    Attributes:
        enabled: Whether LangSmith monitoring is enabled
        api_key: LangSmith API key (required if enabled)
        project: Project name for organizing traces (default: "chatagent-dev")
        api_url: Optional custom API endpoint URL
    """
    
    enabled: bool = Field(default=False)
    api_key: Optional[str] = Field(default=None)
    project: str = Field(default="chatagent-dev")
    api_url: Optional[str] = Field(default=None)
    
    @classmethod
    def from_env(cls) -> "LangSmithConfig":
        """Load LangSmith configuration from environment variables.
        
        Returns:
            LangSmithConfig instance with settings from environment.
        """
        api_key = os.getenv("LANGSMITH_API_KEY", "").strip()
        enabled = bool(api_key and not api_key.startswith("your-"))
        
        project = os.getenv("LANGSMITH_PROJECT", "chatagent-dev").strip()
        if not project:
            project = "chatagent-dev"
        
        api_url = os.getenv("LANGSMITH_API_URL", "").strip()
        if not api_url:
            api_url = None
        
        return cls(
            enabled=enabled,
            api_key=api_key if enabled else None,
            project=project,
            api_url=api_url,
        )
    
    def get_tracer(self):
        """Get LangSmith tracer instance if monitoring is enabled.
        
        Returns:
            LangChainTracer instance if enabled, None otherwise.
        """
        if not self.enabled or not self.api_key:
            return None
        
        try:
            from langsmith import Client
            from langchain_core.tracers import LangChainTracer
            
            client = Client(
                api_key=self.api_key,
                api_url=self.api_url,
            )
            
            tracer = LangChainTracer(
                project_name=self.project,
                client=client,
            )
            
            logger.info(
                f"✅ LangSmith 监控已启用 (项目: {self.project})"
            )
            return tracer
            
        except ImportError:
            logger.warning(
                "⚠️ langsmith 包未安装，LangSmith 监控已禁用。"
                "请运行: pip install langsmith"
            )
            return None
        except Exception as e:
            logger.warning(
                f"⚠️ LangSmith 初始化失败: {e}，继续执行（监控已禁用）"
            )
            return None


# Global config instance (lazy initialization)
_langsmith_config: Optional[LangSmithConfig] = None


def get_langsmith_config() -> LangSmithConfig:
    """Get LangSmith configuration instance.
    
    Returns:
        LangSmithConfig instance (singleton pattern).
    """
    global _langsmith_config
    if _langsmith_config is None:
        _langsmith_config = LangSmithConfig.from_env()
    return _langsmith_config


def get_langsmith_tracer():
    """Get LangSmith tracer instance if monitoring is enabled.
    
    Returns:
        LangChainTracer instance if enabled, None otherwise.
    """
    config = get_langsmith_config()
    return config.get_tracer()


def is_langsmith_enabled() -> bool:
    """Check if LangSmith monitoring is enabled.
    
    Returns:
        True if LangSmith is enabled, False otherwise.
    """
    config = get_langsmith_config()
    return config.enabled

