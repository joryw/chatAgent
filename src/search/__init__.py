"""Web search module for AI Agent."""

from .models import SearchResult, SearchResponse
from .searxng_client import SearXNGClient
from .search_service import SearchService
from .formatter import SearchResultFormatter

__all__ = [
    "SearchResult",
    "SearchResponse",
    "SearXNGClient",
    "SearchService",
    "SearchResultFormatter",
]

