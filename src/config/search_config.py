"""Search configuration management."""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

# Load environment variables
load_dotenv()


class SearchConfig(BaseModel):
    """Configuration for web search functionality.
    
    Attributes:
        enabled: Whether search is enabled by default
        searxng_url: SearXNG instance URL
        timeout: Search request timeout in seconds
        max_results: Maximum number of search results
        max_content_length: Maximum length for result content
        language: Preferred search language
        safesearch: Safe search level (0=off, 1=moderate, 2=strict)
    """
    
    enabled: bool = Field(default=False)
    searxng_url: str = Field(default="https://searx.be")
    timeout: float = Field(default=5.0, gt=0.0, le=30.0)
    max_results: int = Field(default=5, gt=0, le=20)
    max_content_length: int = Field(default=200, gt=0, le=1000)
    language: str = Field(default="auto")
    safesearch: int = Field(default=1, ge=0, le=2)
    
    @validator("timeout")
    def validate_timeout(cls, v: float) -> float:
        """Ensure timeout is reasonable."""
        if v <= 0 or v > 30:
            raise ValueError("Timeout must be between 0 and 30 seconds")
        return v
    
    @validator("max_results")
    def validate_max_results(cls, v: int) -> int:
        """Ensure max_results is reasonable."""
        if v <= 0 or v > 20:
            raise ValueError("max_results must be between 1 and 20")
        return v
    
    @validator("safesearch")
    def validate_safesearch(cls, v: int) -> int:
        """Ensure safesearch level is valid."""
        if v not in [0, 1, 2]:
            raise ValueError("safesearch must be 0, 1, or 2")
        return v
    
    class Config:
        """Pydantic config."""
        protected_namespaces = ()


def get_search_config() -> SearchConfig:
    """Get search configuration from environment variables.
    
    Returns:
        SearchConfig instance with settings loaded from environment.
    """
    return SearchConfig(
        enabled=os.getenv("SEARCH_ENABLED", "false").lower() == "true",
        searxng_url=os.getenv("SEARXNG_URL", "https://searx.be"),
        timeout=float(os.getenv("SEARCH_TIMEOUT", "5.0")),
        max_results=int(os.getenv("SEARCH_MAX_RESULTS", "5")),
        max_content_length=int(os.getenv("SEARCH_MAX_CONTENT_LENGTH", "200")),
        language=os.getenv("SEARCH_LANGUAGE", "auto"),
        safesearch=int(os.getenv("SEARCH_SAFESEARCH", "1")),
    )


def is_search_available() -> bool:
    """Check if search functionality can be enabled.
    
    This checks if the SearXNG URL is configured.
    
    Returns:
        True if search is available
    """
    searxng_url = os.getenv("SEARXNG_URL", "https://searx.be")
    # Basic validation - just check it's not empty and looks like a URL
    return bool(searxng_url and searxng_url.startswith("http"))

