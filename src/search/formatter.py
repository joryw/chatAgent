"""Search result formatting utilities."""

import logging
from typing import List, Optional

from .models import SearchResult, SearchResponse

logger = logging.getLogger(__name__)


class SearchResultFormatter:
    """Formatter for search results to be injected into prompts."""
    
    def __init__(self, max_content_length: int = 200):
        """Initialize formatter.
        
        Args:
            max_content_length: Maximum length for result content
        """
        self.max_content_length = max_content_length
    
    def format_for_prompt(self, response: SearchResponse) -> str:
        """Format search results for injection into LLM prompt.
        
        Args:
            response: SearchResponse object
        
        Returns:
            Formatted string for prompt injection
        """
        if response.is_empty():
            return self._format_no_results(response.query)
        
        formatted = "[搜索结果]\n"
        formatted += f"基于用户问题，以下是相关的网络搜索结果（共 {response.total_results} 条）：\n\n"
        
        for idx, result in enumerate(response.results, 1):
            formatted += self._format_single_result(idx, result)
            formatted += "\n"
        
        formatted += "[/搜索结果]\n\n"
        formatted += "请参考以上搜索结果回答用户问题。在引用搜索结果时，请使用 [数字] 标记来源。\n"
        
        return formatted
    
    def _format_single_result(self, index: int, result: SearchResult) -> str:
        """Format a single search result.
        
        Args:
            index: Result index (1-based)
            result: SearchResult object
        
        Returns:
            Formatted result string
        """
        # Truncate content if too long
        content = result.content
        if len(content) > self.max_content_length:
            content = content[:self.max_content_length] + "..."
        
        # Extract domain from URL
        domain = self._extract_domain(result.url)
        
        formatted = f"{index}. **{result.title}**\n"
        formatted += f"   来源: {domain}\n"
        formatted += f"   链接: {result.url}\n"
        formatted += f"   摘要: {content}\n"
        
        return formatted
    
    def _format_no_results(self, query: str) -> str:
        """Format message when no results found.
        
        Args:
            query: Search query
        
        Returns:
            Formatted message
        """
        return f"[搜索结果]\n未找到与查询 \"{query}\" 相关的搜索结果。\n[/搜索结果]\n\n"
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: Full URL
        
        Returns:
            Domain name
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url
    
    def format_sources_display(self, response: SearchResponse) -> str:
        """Format search sources for display in UI.
        
        Args:
            response: SearchResponse object
        
        Returns:
            Formatted sources string for display
        """
        if response.is_empty():
            return ""
        
        formatted = "### 🔍 搜索来源\n\n"
        
        for idx, result in enumerate(response.results, 1):
            domain = self._extract_domain(result.url)
            formatted += f"{idx}. [{result.title}]({result.url})\n"
            formatted += f"   来源: `{domain}`\n"
            
            # Add short content preview
            preview = result.content[:100] + "..." if len(result.content) > 100 else result.content
            if preview:
                formatted += f"   摘要: {preview}\n"
            
            formatted += "\n"
        
        return formatted

