"""Citation processing for inline reference links."""

import logging
import re
from typing import Dict, List, Set
from urllib.parse import urlparse

from .models import SearchResponse

logger = logging.getLogger(__name__)


class CitationProcessor:
    """Process and convert citations in model responses."""
    
    def __init__(self, search_response: SearchResponse, offset: int = 0):
        """Initialize with search results.
        
        Args:
            search_response: SearchResponse containing URLs for citations
            offset: Starting offset for citation numbering (default: 0, starts from 1)
                   For Agent mode with global numbering, pass the offset from
                   GlobalCitationManager. For Chat mode, use default 0.
                   
        Example:
            # Chat mode (default): citations numbered [1, 2, 3, ...]
            processor = CitationProcessor(search_response)
            
            # Agent mode: citations numbered [6, 7, 8, ...] if offset=5
            processor = CitationProcessor(search_response, offset=5)
        """
        self.search_response = search_response
        self.offset = offset
        self.citation_map: Dict[int, Dict[str, str]] = {}
        self._build_citation_map()
    
    def _build_citation_map(self) -> None:
        """Build mapping from citation number to URL and metadata.
        
        Citation numbers start from (offset + 1). For example:
        - offset=0: citations are [1, 2, 3, ...]
        - offset=5: citations are [6, 7, 8, ...]
        """
        if self.search_response.is_empty():
            logger.debug("No search results to build citation map")
            return
        
        for idx, result in enumerate(self.search_response.results, 1):
            citation_num = self.offset + idx
            self.citation_map[citation_num] = {
                'url': result.url,
                'title': result.title,
                'domain': self._extract_domain(result.url)
            }
        
        if self.offset > 0:
            logger.info(
                f"Built citation map with {len(self.citation_map)} entries "
                f"(offset={self.offset}, range=[{self.offset+1}-{self.offset+len(self.citation_map)}])"
            )
        else:
            logger.info(f"Built citation map with {len(self.citation_map)} entries")
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: Full URL
        
        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception as e:
            logger.warning(f"Failed to parse URL {url}: {e}")
            return url
    
    def convert_citations(self, text: str) -> str:
        """Convert [num] to [[num]](url) format.
        
        Args:
            text: Original text with citations
        
        Returns:
            Text with clickable citation links
        """
        if not self.citation_map:
            logger.debug("No citation map available, skipping conversion")
            return text
        
        def replace_citation(match):
            """Replace citation with markdown link."""
            num = int(match.group(1))
            if num in self.citation_map:
                url = self.citation_map[num]['url']
                # Use [[num]](url) format to keep the bracket notation
                return f"[[{num}]]({url})"
            else:
                # Keep original if citation number not found
                logger.warning(f"Citation [{num}] not found in search results")
                return match.group(0)
        
        # Pattern matches [number] where number is one or more digits
        pattern = r'\[(\d+)\]'
        converted = re.sub(pattern, replace_citation, text)
        
        # Log conversion statistics
        citations_found = len(re.findall(pattern, text))
        logger.info(f"Converted {citations_found} citation(s) in response")
        
        return converted
    
    def _extract_citations(self, text: str) -> Set[int]:
        """Extract all citation numbers used in text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Set of citation numbers found
        """
        pattern = r'\[(\d+)\]'
        matches = re.finditer(pattern, text)
        return {int(match.group(1)) for match in matches}
    
    def get_citations_list(self, text: str) -> str:
        """Generate formatted citations list for display.
        
        Args:
            text: Text to extract citations from
        
        Returns:
            Formatted citations section (empty string if no citations)
        """
        if not self.citation_map:
            return ""
        
        # Extract citation numbers actually used in the text
        cited_nums = self._extract_citations(text)
        
        # Filter to only valid citations
        valid_citations = {
            num for num in cited_nums 
            if num in self.citation_map
        }
        
        if not valid_citations:
            logger.debug("No valid citations found in text")
            return ""
        
        # Build formatted citations list
        citations = "\n\n---\n**📚 参考文献:**\n"
        
        for num in sorted(valid_citations):
            info = self.citation_map[num]
            citations += f"\n{num}. [{info['title']}]({info['url']}) - `{info['domain']}`"
        
        logger.info(f"Generated citations list with {len(valid_citations)} reference(s)")
        
        return citations
    
    def process_response(self, text: str) -> str:
        """Full processing: convert citations and add reference list.
        
        Args:
            text: Original response text
        
        Returns:
            Processed text with clickable citations and reference list
        """
        # Convert inline citations
        converted = self.convert_citations(text)
        
        # Add citations list at the end
        citations_list = self.get_citations_list(converted)
        
        return converted + citations_list

