"""Data models for search results."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SearchResult:
    """Represents a single search result."""
    
    title: str
    url: str
    content: str
    engine: Optional[str] = None
    score: Optional[float] = None
    
    def __str__(self) -> str:
        """String representation of search result."""
        return f"{self.title}\n{self.url}\n{self.content[:200]}..."


@dataclass
class SearchResponse:
    """Represents a complete search response."""
    
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    
    def __str__(self) -> str:
        """String representation of search response."""
        return f"Query: {self.query}\nResults: {self.total_results} ({self.search_time:.2f}s)"
    
    def is_empty(self) -> bool:
        """Check if search returned no results."""
        return len(self.results) == 0

