"""Tests for CitationProcessor offset functionality."""

import pytest
from src.search.citation_processor import CitationProcessor
from src.search.models import SearchResponse, SearchResult


@pytest.fixture
def sample_search_response():
    """Create sample search response."""
    results = [
        SearchResult(
            url="https://example.com/1",
            title="Article 1",
            content="Content of article 1",
            score=0.9
        ),
        SearchResult(
            url="https://example.com/2",
            title="Article 2",
            content="Content of article 2",
            score=0.8
        ),
        SearchResult(
            url="https://example.com/3",
            title="Article 3",
            content="Content of article 3",
            score=0.7
        ),
    ]
    return SearchResponse(
        results=results,
        total_count=3,
        query="test query"
    )


def test_citation_processor_default_offset(sample_search_response):
    """Test CitationProcessor with default offset (0)."""
    processor = CitationProcessor(sample_search_response)
    
    # Check citation map starts from 1
    assert 1 in processor.citation_map
    assert 2 in processor.citation_map
    assert 3 in processor.citation_map
    assert 4 not in processor.citation_map
    
    # Check URLs
    assert processor.citation_map[1]['url'] == "https://example.com/1"
    assert processor.citation_map[2]['url'] == "https://example.com/2"
    assert processor.citation_map[3]['url'] == "https://example.com/3"


def test_citation_processor_with_offset(sample_search_response):
    """Test CitationProcessor with custom offset."""
    # Offset of 5 means citations start from 6
    processor = CitationProcessor(sample_search_response, offset=5)
    
    # Check citation map starts from 6
    assert 1 not in processor.citation_map
    assert 5 not in processor.citation_map
    assert 6 in processor.citation_map
    assert 7 in processor.citation_map
    assert 8 in processor.citation_map
    assert 9 not in processor.citation_map
    
    # Check URLs
    assert processor.citation_map[6]['url'] == "https://example.com/1"
    assert processor.citation_map[7]['url'] == "https://example.com/2"
    assert processor.citation_map[8]['url'] == "https://example.com/3"


def test_citation_processor_offset_zero(sample_search_response):
    """Test CitationProcessor with explicit offset=0."""
    processor = CitationProcessor(sample_search_response, offset=0)
    
    # Should be same as default
    assert 1 in processor.citation_map
    assert 2 in processor.citation_map
    assert 3 in processor.citation_map


def test_convert_citations_with_offset(sample_search_response):
    """Test citation conversion with offset."""
    processor = CitationProcessor(sample_search_response, offset=5)
    
    # Text with citations [6], [7], [8]
    text = "According to [6] and [7], with reference to [8]."
    converted = processor.convert_citations(text)
    
    # Should convert to clickable links
    assert "[[6]](https://example.com/1)" in converted
    assert "[[7]](https://example.com/2)" in converted
    assert "[[8]](https://example.com/3)" in converted


def test_convert_citations_with_invalid_numbers(sample_search_response):
    """Test citation conversion with invalid citation numbers."""
    processor = CitationProcessor(sample_search_response, offset=5)
    
    # Text with valid [6] and invalid [1], [10]
    text = "Valid [6] and invalid [1] [10]."
    converted = processor.convert_citations(text)
    
    # Valid citation should be converted
    assert "[[6]](https://example.com/1)" in converted
    
    # Invalid citations should remain unchanged
    assert "[1]" in converted
    assert "[10]" in converted
    # But make sure they're not converted
    assert "[[1]]" not in converted
    assert "[[10]]" not in converted


def test_get_citations_list_with_offset(sample_search_response):
    """Test citations list generation with offset."""
    processor = CitationProcessor(sample_search_response, offset=5)
    
    # Text using citations [6] and [8]
    text = "Reference [6] and [8]."
    citations_list = processor.get_citations_list(text)
    
    # Should include used citations
    assert "6. [Article 1](https://example.com/1)" in citations_list
    assert "8. [Article 3](https://example.com/3)" in citations_list
    
    # Should not include unused citation [7]
    assert "7. [Article 2]" not in citations_list


def test_process_response_with_offset(sample_search_response):
    """Test full response processing with offset."""
    processor = CitationProcessor(sample_search_response, offset=10)
    
    # Response text with citations [11] and [12]
    text = "Based on research [11] and studies [12], we conclude..."
    processed = processor.process_response(text)
    
    # Should have converted citations
    assert "[[11]](https://example.com/1)" in processed
    assert "[[12]](https://example.com/2)" in processed
    
    # Should have citations list at the end
    assert "📚 参考文献:" in processed
    assert "11. [Article 1](https://example.com/1)" in processed
    assert "12. [Article 2](https://example.com/2)" in processed


def test_multiple_processors_with_different_offsets(sample_search_response):
    """Test using multiple processors with different offsets (simulating multiple searches)."""
    # First search: offset=0, citations [1-3]
    processor1 = CitationProcessor(sample_search_response, offset=0)
    assert list(processor1.citation_map.keys()) == [1, 2, 3]
    
    # Second search: offset=3, citations [4-6]
    processor2 = CitationProcessor(sample_search_response, offset=3)
    assert list(processor2.citation_map.keys()) == [4, 5, 6]
    
    # Third search: offset=6, citations [7-9]
    processor3 = CitationProcessor(sample_search_response, offset=6)
    assert list(processor3.citation_map.keys()) == [7, 8, 9]


def test_large_offset(sample_search_response):
    """Test CitationProcessor with large offset."""
    processor = CitationProcessor(sample_search_response, offset=100)
    
    # Should handle large offsets correctly
    assert 101 in processor.citation_map
    assert 102 in processor.citation_map
    assert 103 in processor.citation_map
    
    text = "Reference [101] and [103]."
    converted = processor.convert_citations(text)
    
    assert "[[101]](https://example.com/1)" in converted
    assert "[[103]](https://example.com/3)" in converted


def test_empty_search_response_with_offset():
    """Test CitationProcessor with empty results and offset."""
    empty_response = SearchResponse(
        results=[],
        total_count=0,
        query="empty query"
    )
    
    processor = CitationProcessor(empty_response, offset=5)
    
    # Should have empty citation map
    assert len(processor.citation_map) == 0
    
    # Should return empty citations list
    text = "Some text [6]."
    citations_list = processor.get_citations_list(text)
    assert citations_list == ""


def test_backward_compatibility():
    """Test that CitationProcessor works without offset parameter (backward compatibility)."""
    results = [
        SearchResult(
            url="https://example.com/1",
            title="Article 1",
            content="Content",
            score=0.9
        ),
    ]
    response = SearchResponse(results=results, total_count=1, query="test")
    
    # Should work without offset parameter
    processor = CitationProcessor(response)
    
    # Should default to offset=0, starting from 1
    assert 1 in processor.citation_map
    assert processor.citation_map[1]['url'] == "https://example.com/1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

