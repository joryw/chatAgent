"""Global citation manager for Agent mode multi-round search."""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from .models import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class SearchRound:
    """Represents a single search round with its results."""
    
    round_number: int
    query: str
    results: List[SearchResult]
    start_number: int
    end_number: int


@dataclass
class GlobalCitationManager:
    """Manages citations across multiple search rounds in Agent mode.
    
    This class assigns unique, sequential global numbers to all search results
    from multiple search rounds, and generates a unified citation list.
    
    Example:
        >>> manager = GlobalCitationManager()
        >>> start, end = manager.add_search_results(results1, "AI models 2024")
        >>> # Returns (1, 5) if 5 results
        >>> start, end = manager.add_search_results(results2, "AI benchmarks")
        >>> # Returns (6, 10) - continues from previous
        >>> citations = manager.generate_citations_list([1, 4, 7])
        >>> # Generates formatted list with only used citations
    """
    
    _search_rounds: List[SearchRound] = field(default_factory=list)
    _current_number: int = field(default=1)
    _citation_map: Dict[int, Dict[str, str]] = field(default_factory=dict)
    
    def add_search_results(
        self, 
        results: List[SearchResult], 
        query: str
    ) -> Tuple[int, int]:
        """Add search results and assign global numbers.
        
        Args:
            results: List of search results from one search round
            query: The search query that produced these results
            
        Returns:
            Tuple of (start_number, end_number) for these results
            
        Example:
            >>> manager = GlobalCitationManager()
            >>> start, end = manager.add_search_results(results, "AI news")
            >>> print(f"Results numbered [{start}-{end}]")
            Results numbered [1-5]
        """
        if not results:
            logger.warning(f"添加空搜索结果集，查询: {query}")
            return (0, 0)
        
        start_number = self._current_number
        round_number = len(self._search_rounds) + 1
        
        # Build citation map for these results
        for idx, result in enumerate(results):
            global_num = self._current_number
            self._citation_map[global_num] = {
                'url': result.url,
                'title': result.title,
                'domain': self._extract_domain(result.url),
                'content': result.content[:200] + "..." if len(result.content) > 200 else result.content,
                'query': query,
                'round': round_number
            }
            self._current_number += 1
        
        end_number = self._current_number - 1
        
        # Store this search round
        search_round = SearchRound(
            round_number=round_number,
            query=query,
            results=results,
            start_number=start_number,
            end_number=end_number
        )
        self._search_rounds.append(search_round)
        
        logger.info(
            f"🔢 添加第 {round_number} 次搜索结果: "
            f"{len(results)} 条结果, 编号 [{start_number}-{end_number}]"
        )
        
        return (start_number, end_number)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: Full URL
            
        Returns:
            Domain name
        """
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception as e:
            logger.warning(f"Failed to parse URL {url}: {e}")
            return url
    
    def get_offset_for_round(self, round_number: int) -> int:
        """Get the starting offset for a specific round.
        
        Args:
            round_number: The round number (1-indexed)
            
        Returns:
            Starting number for that round (0 if round not found)
        """
        for search_round in self._search_rounds:
            if search_round.round_number == round_number:
                return search_round.start_number - 1  # offset is 0-indexed
        return 0
    
    def get_current_offset(self) -> int:
        """Get current offset (next available number - 1).
        
        Returns:
            Current offset value for next search
        """
        return self._current_number - 1
    
    def generate_citations_list(
        self, 
        used_numbers: Optional[List[int]] = None,
        include_unused: bool = False
    ) -> str:
        """Generate formatted citations list.
        
        Args:
            used_numbers: List of citation numbers actually used in the response.
                         If None, includes all citations.
            include_unused: If True, includes all citations even if not used
            
        Returns:
            Formatted citations section with grouped by search round
            
        Example:
            >>> citations = manager.generate_citations_list([1, 4, 7])
            ---
            **📚 引用文章列表:**
            
            **第 1 次搜索** (查询: AI models 2024)
            1. [GPT-4 Turbo](https://openai.com/...) - `openai.com`
            
            **第 2 次搜索** (查询: AI benchmarks)
            4. [MMLU Results](https://huggingface.co/...) - `huggingface.co`
        """
        if not self._citation_map:
            logger.debug("没有引用可生成列表")
            return ""
        
        # Determine which citations to include
        if include_unused or used_numbers is None:
            citations_to_include = set(self._citation_map.keys())
        else:
            # Only include citations that were actually used
            citations_to_include = {
                num for num in used_numbers 
                if num in self._citation_map
            }
        
        if not citations_to_include:
            logger.debug("没有有效的引用编号")
            return ""
        
        # Build citations list grouped by search round
        citations_text = "\n\n---\n**📚 引用文章列表:**\n"
        
        for search_round in self._search_rounds:
            # Find citations from this round that should be included
            round_citations = [
                num for num in range(search_round.start_number, search_round.end_number + 1)
                if num in citations_to_include
            ]
            
            if not round_citations:
                continue
            
            # Add round header
            citations_text += f"\n**第 {search_round.round_number} 次搜索** (查询: {search_round.query})\n"
            
            # Add each citation from this round
            for num in sorted(round_citations):
                info = self._citation_map[num]
                citations_text += f"{num}. [{info['title']}]({info['url']}) - `{info['domain']}`\n"
        
        logger.info(f"✅ 生成引用列表: {len(citations_to_include)} 条引用")
        
        return citations_text
    
    def get_global_citation_map(self) -> Dict[int, Dict[str, str]]:
        """Get the complete global citation map.
        
        Returns:
            Dictionary mapping citation numbers to their metadata
        """
        return self._citation_map.copy()
    
    def get_citation_info(self, number: int) -> Optional[Dict[str, str]]:
        """Get information for a specific citation number.
        
        Args:
            number: Global citation number
            
        Returns:
            Citation info dict or None if not found
        """
        return self._citation_map.get(number)
    
    def get_total_citations(self) -> int:
        """Get total number of citations stored.
        
        Returns:
            Total citation count
        """
        return len(self._citation_map)
    
    def get_search_rounds_count(self) -> int:
        """Get number of search rounds.
        
        Returns:
            Number of search rounds
        """
        return len(self._search_rounds)
    
    def reset(self) -> None:
        """Reset the citation manager to initial state.
        
        This should be called when starting a new conversation or
        when switching modes.
        """
        self._search_rounds.clear()
        self._current_number = 1
        self._citation_map.clear()
        logger.info("🔄 重置全局引用管理器")
    
    def get_state(self) -> Dict:
        """Get current state for debugging/logging.
        
        Returns:
            Dictionary with current state information
        """
        return {
            'total_citations': self.get_total_citations(),
            'search_rounds': self.get_search_rounds_count(),
            'next_number': self._current_number,
            'rounds': [
                {
                    'round': r.round_number,
                    'query': r.query,
                    'range': f"[{r.start_number}-{r.end_number}]",
                    'count': len(r.results)
                }
                for r in self._search_rounds
            ]
        }

