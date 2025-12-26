"""SearXNG API client."""

import logging
from typing import Optional, Dict, Any, List
import httpx

from .models import SearchResult, SearchResponse

logger = logging.getLogger(__name__)


class SearXNGClient:
    """Client for SearXNG search engine API."""
    
    def __init__(
        self,
        base_url: str = "https://searx.be",
        timeout: float = 5.0,
        max_results: int = 5,
    ):
        """Initialize SearXNG client.
        
        Args:
            base_url: SearXNG instance URL
            timeout: Request timeout in seconds
            max_results: Maximum number of results to return
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_results = max_results
        self.search_url = f"{self.base_url}/search"
        
        logger.info(f"Initialized SearXNG client with base URL: {self.base_url}")
    
    async def search(
        self,
        query: str,
        language: str = "auto",
        safesearch: int = 1,
    ) -> Optional[SearchResponse]:
        """Perform a search query.
        
        Args:
            query: Search query string
            language: Search language (default: auto)
            safesearch: Safe search level (0=off, 1=moderate, 2=strict)
        
        Returns:
            SearchResponse object or None if search fails
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return None
        
        params = {
            "q": query,
            "format": "json",
            "language": language,
            "safesearch": safesearch,
        }
        
        try:
            logger.info(f"Searching for: {query}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.search_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_response(query, data)
        
        except httpx.TimeoutException:
            logger.error(f"Search request timed out after {self.timeout}s")
            return None
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during search: {str(e)}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            return None
    
    def _parse_response(self, query: str, data: Dict[str, Any]) -> SearchResponse:
        """Parse SearXNG JSON response.
        
        Args:
            query: Original search query
            data: JSON response data
        
        Returns:
            SearchResponse object
        """
        results = []
        raw_results = data.get("results", [])
        
        # Limit results
        for item in raw_results[:self.max_results]:
            try:
                result = SearchResult(
                    title=item.get("title", "No title"),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    engine=item.get("engine", "unknown"),
                    score=item.get("score", 0.0),
                )
                results.append(result)
            
            except Exception as e:
                logger.warning(f"Failed to parse search result: {str(e)}")
                continue
        
        search_time = data.get("timing", {}).get("total", 0.0)
        
        logger.info(f"Parsed {len(results)} search results")
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_time=search_time,
        )
    
    async def health_check(self) -> bool:
        """Check if SearXNG service is available.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(self.base_url)
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

