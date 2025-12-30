"""Tests for GlobalCitationManager."""

import pytest
from src.search.global_citation_manager import GlobalCitationManager, SearchRound
from src.search.models import SearchResult


@pytest.fixture
def sample_results_round1():
    """Create sample search results for round 1."""
    return [
        SearchResult(
            url="https://openai.com/gpt4",
            title="GPT-4 Release",
            content="GPT-4 is the latest model from OpenAI with improved reasoning capabilities.",
            score=0.95
        ),
        SearchResult(
            url="https://anthropic.com/claude3",
            title="Claude 3 Announcement",
            content="Claude 3 represents a major advancement in AI capabilities.",
            score=0.92
        ),
        SearchResult(
            url="https://deepseek.com/v2",
            title="DeepSeek V2 Review",
            content="DeepSeek V2 offers competitive performance at lower cost.",
            score=0.90
        ),
    ]


@pytest.fixture
def sample_results_round2():
    """Create sample search results for round 2."""
    return [
        SearchResult(
            url="https://huggingface.co/benchmarks",
            title="AI Benchmarks 2024",
            content="Comprehensive benchmarks for AI models including MMLU and HumanEval.",
            score=0.88
        ),
        SearchResult(
            url="https://techcrunch.com/ai-costs",
            title="AI Model Costs Comparison",
            content="Comparing the pricing of major AI models.",
            score=0.85
        ),
    ]


def test_initialization():
    """Test GlobalCitationManager initialization."""
    manager = GlobalCitationManager()
    assert manager.get_total_citations() == 0
    assert manager.get_search_rounds_count() == 0
    assert manager.get_current_offset() == 0


def test_add_single_search_round(sample_results_round1):
    """Test adding a single search round."""
    manager = GlobalCitationManager()
    
    start, end = manager.add_search_results(sample_results_round1, "AI models 2024")
    
    # Should assign numbers [1-3]
    assert start == 1
    assert end == 3
    assert manager.get_total_citations() == 3
    assert manager.get_search_rounds_count() == 1
    assert manager.get_current_offset() == 3


def test_add_multiple_search_rounds(sample_results_round1, sample_results_round2):
    """Test adding multiple search rounds with continuous numbering."""
    manager = GlobalCitationManager()
    
    # First round: [1-3]
    start1, end1 = manager.add_search_results(sample_results_round1, "AI models 2024")
    assert start1 == 1
    assert end1 == 3
    
    # Second round: [4-5]
    start2, end2 = manager.add_search_results(sample_results_round2, "AI benchmarks")
    assert start2 == 4
    assert end2 == 5
    
    assert manager.get_total_citations() == 5
    assert manager.get_search_rounds_count() == 2


def test_add_empty_results():
    """Test adding empty search results."""
    manager = GlobalCitationManager()
    
    start, end = manager.add_search_results([], "empty query")
    
    # Should return (0, 0) for empty results
    assert start == 0
    assert end == 0
    assert manager.get_total_citations() == 0


def test_get_citation_info(sample_results_round1):
    """Test retrieving citation information."""
    manager = GlobalCitationManager()
    manager.add_search_results(sample_results_round1, "test query")
    
    # Get first citation
    info = manager.get_citation_info(1)
    assert info is not None
    assert info['url'] == "https://openai.com/gpt4"
    assert info['title'] == "GPT-4 Release"
    assert 'domain' in info
    assert 'content' in info
    
    # Get non-existent citation
    info = manager.get_citation_info(999)
    assert info is None


def test_generate_citations_list_with_used_numbers(sample_results_round1, sample_results_round2):
    """Test generating citations list with specific used numbers."""
    manager = GlobalCitationManager()
    manager.add_search_results(sample_results_round1, "AI models 2024")
    manager.add_search_results(sample_results_round2, "AI benchmarks")
    
    # Generate list for citations [1, 3, 5]
    citations = manager.generate_citations_list([1, 3, 5])
    
    assert "📚 引用文章列表" in citations
    assert "第 1 次搜索" in citations
    assert "第 2 次搜索" in citations
    assert "GPT-4 Release" in citations
    assert "DeepSeek V2 Review" in citations
    assert "AI Model Costs Comparison" in citations
    
    # Should not include unused citations [2, 4]
    assert "Claude 3 Announcement" not in citations
    assert "AI Benchmarks 2024" not in citations


def test_generate_citations_list_all(sample_results_round1):
    """Test generating citations list with all citations."""
    manager = GlobalCitationManager()
    manager.add_search_results(sample_results_round1, "test query")
    
    # Generate with include_unused=True
    citations = manager.generate_citations_list(include_unused=True)
    
    assert "📚 引用文章列表" in citations
    assert "GPT-4 Release" in citations
    assert "Claude 3 Announcement" in citations
    assert "DeepSeek V2 Review" in citations


def test_generate_citations_list_empty():
    """Test generating citations list with no citations."""
    manager = GlobalCitationManager()
    
    citations = manager.generate_citations_list([])
    
    # Should return empty string
    assert citations == ""


def test_reset(sample_results_round1, sample_results_round2):
    """Test resetting the citation manager."""
    manager = GlobalCitationManager()
    manager.add_search_results(sample_results_round1, "query 1")
    manager.add_search_results(sample_results_round2, "query 2")
    
    assert manager.get_total_citations() == 5
    assert manager.get_search_rounds_count() == 2
    
    # Reset
    manager.reset()
    
    assert manager.get_total_citations() == 0
    assert manager.get_search_rounds_count() == 0
    assert manager.get_current_offset() == 0


def test_get_offset_for_round(sample_results_round1, sample_results_round2):
    """Test getting offset for specific round."""
    manager = GlobalCitationManager()
    manager.add_search_results(sample_results_round1, "query 1")  # [1-3]
    manager.add_search_results(sample_results_round2, "query 2")  # [4-5]
    
    # Round 1 starts at 1, so offset is 0
    assert manager.get_offset_for_round(1) == 0
    
    # Round 2 starts at 4, so offset is 3
    assert manager.get_offset_for_round(2) == 3
    
    # Non-existent round
    assert manager.get_offset_for_round(999) == 0


def test_get_state(sample_results_round1, sample_results_round2):
    """Test getting current state."""
    manager = GlobalCitationManager()
    manager.add_search_results(sample_results_round1, "AI models")
    manager.add_search_results(sample_results_round2, "AI benchmarks")
    
    state = manager.get_state()
    
    assert state['total_citations'] == 5
    assert state['search_rounds'] == 2
    assert state['next_number'] == 6
    assert len(state['rounds']) == 2
    
    # Check first round info
    round1 = state['rounds'][0]
    assert round1['round'] == 1
    assert round1['query'] == "AI models"
    assert round1['range'] == "[1-3]"
    assert round1['count'] == 3
    
    # Check second round info
    round2 = state['rounds'][1]
    assert round2['round'] == 2
    assert round2['query'] == "AI benchmarks"
    assert round2['range'] == "[4-5]"
    assert round2['count'] == 2


def test_extract_domain():
    """Test domain extraction from URLs."""
    manager = GlobalCitationManager()
    
    # Test various URL formats
    assert "openai.com" in manager._extract_domain("https://openai.com/gpt4")
    assert "www.github.com" in manager._extract_domain("https://www.github.com/repo")
    assert "api.example.com" in manager._extract_domain("http://api.example.com:8080/path")
    
    # Test invalid URL
    result = manager._extract_domain("not a url")
    assert result == "not a url"  # Falls back to original


def test_citation_numbering_with_three_rounds(sample_results_round1, sample_results_round2):
    """Test citation numbering across three search rounds."""
    manager = GlobalCitationManager()
    
    # Round 1: [1-3]
    start1, end1 = manager.add_search_results(sample_results_round1, "query 1")
    assert (start1, end1) == (1, 3)
    
    # Round 2: [4-5]
    start2, end2 = manager.add_search_results(sample_results_round2, "query 2")
    assert (start2, end2) == (4, 5)
    
    # Round 3: [6-8] (using round1 results again)
    start3, end3 = manager.add_search_results(sample_results_round1, "query 3")
    assert (start3, end3) == (6, 8)
    
    # Total should be 8 citations
    assert manager.get_total_citations() == 8
    assert manager.get_search_rounds_count() == 3


def test_citations_list_formatting(sample_results_round1, sample_results_round2):
    """Test the formatting of citations list."""
    manager = GlobalCitationManager()
    manager.add_search_results(sample_results_round1, "AI models 2024")
    manager.add_search_results(sample_results_round2, "AI benchmarks")
    
    # Use citations [1, 4]
    citations = manager.generate_citations_list([1, 4])
    
    # Check structure
    assert citations.startswith("\n\n---\n**📚 引用文章列表:**\n")
    
    # Check round headers
    assert "**第 1 次搜索**" in citations
    assert "(查询: AI models 2024)" in citations
    assert "**第 2 次搜索**" in citations
    assert "(查询: AI benchmarks)" in citations
    
    # Check citation format
    assert "1. [GPT-4 Release](https://openai.com/gpt4)" in citations
    assert "`openai.com`" in citations
    assert "4. [AI Benchmarks 2024](https://huggingface.co/benchmarks)" in citations
    assert "`huggingface.co`" in citations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

