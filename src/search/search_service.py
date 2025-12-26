"""Main search service orchestrating search operations."""

import logging
from typing import Optional

from .models import SearchResponse
from .searxng_client import SearXNGClient
from .formatter import SearchResultFormatter

logger = logging.getLogger(__name__)


class SearchService:
    """Service for handling web search operations."""
    
    def __init__(
        self,
        searxng_url: str = "https://searx.be",
        timeout: float = 5.0,
        max_results: int = 5,
        max_content_length: int = 200,
    ):
        """Initialize search service.
        
        Args:
            searxng_url: SearXNG instance URL
            timeout: Search request timeout
            max_results: Maximum number of results
            max_content_length: Maximum length for result content
        """
        self.client = SearXNGClient(
            base_url=searxng_url,
            timeout=timeout,
            max_results=max_results,
        )
        self.formatter = SearchResultFormatter(
            max_content_length=max_content_length,
        )
        
        logger.info("Search service initialized")
    
    async def search(self, query: str) -> Optional[SearchResponse]:
        """Perform a web search.
        
        Args:
            query: Search query
        
        Returns:
            SearchResponse or None if search fails
        """
        try:
            logger.info(f"Performing search: {query}")
            response = await self.client.search(query)
            
            if response:
                logger.info(f"Search completed: {response.total_results} results")
            else:
                logger.warning("Search returned no response")
            
            return response
        
        except Exception as e:
            logger.error(f"Search service error: {str(e)}")
            return None
    
    def format_for_prompt(self, response: Optional[SearchResponse]) -> str:
        """Format search results for LLM prompt injection.
        
        Args:
            response: SearchResponse or None
        
        Returns:
            Formatted string for prompt
        """
        if not response:
            return ""
        
        return self.formatter.format_for_prompt(response)
    
    def format_sources(self, response: Optional[SearchResponse]) -> str:
        """Format search sources for UI display.
        
        Args:
            response: SearchResponse or None
        
        Returns:
            Formatted sources string
        """
        if not response:
            return ""
        
        return self.formatter.format_sources_display(response)
    
    async def is_available(self) -> bool:
        """Check if search service is available.
        
        Returns:
            True if service is healthy
        """
        return await self.client.health_check()

