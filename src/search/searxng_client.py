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
        base_url: str = "http://localhost:8080",
        timeout: float = 5.0,
        max_results: int = 5,
    ):
        """Initialize SearXNG client.
        
        Args:
            base_url: SearXNG instance URL (default: local deployment)
            timeout: Request timeout in seconds
            max_results: Maximum number of results to return
        
        Note:
            For stable search functionality, use a local SearXNG deployment.
            See docs/guides/searxng-deployment.md for setup instructions.
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
        """Check if SearXNG service is available and properly configured.
        
        This performs three checks:
        1. Service is reachable (HTTP 200)
        2. JSON API is enabled
        3. Search functionality works
        
        Returns:
            True if service is healthy and properly configured, False otherwise
        """
        try:
            logger.debug(f"Performing health check for SearXNG at {self.base_url}")
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check 1: Service is reachable
                try:
                    response = await client.get(self.base_url)
                    if response.status_code != 200:
                        logger.error(
                            f"❌ SearXNG service returned HTTP {response.status_code}. "
                            "Please check if the service is running."
                        )
                        return False
                    logger.debug("✅ SearXNG service is reachable")
                except httpx.ConnectError:
                    logger.error(
                        f"❌ Cannot connect to SearXNG at {self.base_url}. "
                        "Please ensure:\n"
                        "  1. SearXNG is deployed and running\n"
                        "  2. The URL is correct (default: http://localhost:8080)\n"
                        "  3. No firewall is blocking the connection\n"
                        "  📖 See: docs/guides/searxng-deployment.md"
                    )
                    return False
                
                # Check 2: JSON API is enabled
                try:
                    test_params = {"q": "test", "format": "json"}
                    api_response = await client.get(
                        f"{self.base_url}/search",
                        params=test_params
                    )
                    
                    if api_response.status_code != 200:
                        logger.error(
                            f"❌ SearXNG API returned HTTP {api_response.status_code}"
                        )
                        return False
                    
                    # Try to parse as JSON
                    try:
                        data = api_response.json()
                        
                        # Check if it looks like a valid SearXNG response
                        if "results" not in data:
                            logger.error(
                                "❌ JSON API returned unexpected format. "
                                "Please check settings.yml:\n"
                                "  search:\n"
                                "    formats:\n"
                                "      - json  # <-- Ensure 'json' is present\n"
                                "  enable_api: true  # <-- Must be true\n"
                                "Then restart SearXNG container."
                            )
                            return False
                        
                        logger.debug("✅ JSON API is enabled and working")
                        logger.debug(f"✅ Test search returned {len(data.get('results', []))} results")
                        return True
                    
                    except ValueError:
                        logger.error(
                            "❌ SearXNG did not return valid JSON. "
                            "This usually means JSON format is not enabled.\n"
                            "Please check your settings.yml:\n"
                            "  search:\n"
                            "    formats:\n"
                            "      - json  # <-- Add this if missing\n"
                            "Then restart: docker compose restart searxng"
                        )
                        return False
                
                except httpx.HTTPError as e:
                    logger.error(f"❌ HTTP error during API check: {str(e)}")
                    return False
        
        except httpx.TimeoutException:
            logger.error(
                f"❌ Health check timed out after 5 seconds. "
                "The SearXNG instance may be overloaded or unreachable."
            )
            return False
        
        except Exception as e:
            logger.error(f"❌ Unexpected error during health check: {str(e)}")
            return False

