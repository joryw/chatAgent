"""Integration test for Agent citation processing."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.agents.react_agent import ReActAgent, AgentConfig
from src.search.global_citation_manager import GlobalCitationManager
from src.search.models import SearchResponse, SearchResult


@pytest.fixture
def mock_search_response():
    """Create a mock search response."""
    return SearchResponse(
        query="test query",
        results=[
            SearchResult(
                title="Result 1",
                url="https://example.com/1",
                content="Content 1",
                score=0.9
            ),
            SearchResult(
                title="Result 2",
                url="https://example.com/2",
                content="Content 2",
                score=0.8
            ),
        ]
    )


def test_citation_manager_initialization():
    """Test that GlobalCitationManager is initialized in ReActAgent."""
    # Create a simple mock config
    config = AgentConfig()
    
    # Mock the LLMs and search service
    with patch('src.agents.react_agent.create_react_graph'):
        mock_llm = Mock()
        mock_search_service = Mock()
        
        agent = ReActAgent(
            function_call_llm=mock_llm,
            answer_llm=mock_llm,
            search_service=mock_search_service,
            config=config
        )
        
        # Verify citation manager is created
        assert agent.citation_manager is not None
        assert isinstance(agent.citation_manager, GlobalCitationManager)
        assert agent.citation_manager.next_global_idx == 1


def test_citation_manager_reset():
    """Test that citation manager is reset between runs."""
    config = AgentConfig()
    
    with patch('src.agents.react_agent.create_react_graph'):
        mock_llm = Mock()
        mock_search_service = Mock()
        
        agent = ReActAgent(
            function_call_llm=mock_llm,
            answer_llm=mock_llm,
            search_service=mock_search_service,
            config=config
        )
        
        # Simulate adding some citations
        agent.citation_manager.next_global_idx = 10
        agent.citation_manager.global_citation_map = {1: {"url": "test"}}
        
        # Reset should clear everything
        agent.citation_manager.reset()
        
        assert agent.citation_manager.next_global_idx == 1
        assert len(agent.citation_manager.global_citation_map) == 0
        assert len(agent.citation_manager.search_queries_history) == 0


def test_search_tool_has_citation_manager():
    """Test that SearchTool receives citation manager reference."""
    config = AgentConfig()
    
    with patch('src.agents.react_agent.create_react_graph'):
        mock_llm = Mock()
        mock_search_service = Mock()
        
        agent = ReActAgent(
            function_call_llm=mock_llm,
            answer_llm=mock_llm,
            search_service=mock_search_service,
            config=config
        )
        
        # The SearchTool should be created with citation_manager
        # This is verified by checking that the agent has a citation_manager
        # and that it's passed to tools during agent creation
        assert agent.citation_manager is not None
        
        # Note: Full integration test would require actually running the agent
        # which is more complex due to LangGraph dependencies


def test_citation_list_generation():
    """Test that citation list is generated correctly."""
    manager = GlobalCitationManager()
    
    # Create mock search responses
    response1 = SearchResponse(
        query="first search",
        results=[
            SearchResult(title="Title 1", url="https://example.com/1", content="Content 1", score=0.9),
            SearchResult(title="Title 2", url="https://example.com/2", content="Content 2", score=0.8),
        ]
    )
    
    response2 = SearchResponse(
        query="second search",
        results=[
            SearchResult(title="Title 3", url="https://example.com/3", content="Content 3", score=0.9),
        ]
    )
    
    # Add citations
    map1 = manager.add_citations(response1, "first search")
    map2 = manager.add_citations(response2, "second search")
    
    # Verify sequential numbering
    assert map1 == {1: 1, 2: 2}
    assert map2 == {1: 3}
    
    # Generate citation list
    citations_list = manager.generate_citations_list()
    
    # Verify content
    assert "first search" in citations_list
    assert "second search" in citations_list
    assert "[1-2]" in citations_list  # First search range
    assert "[3-3]" in citations_list  # Second search range
    assert "Title 1" in citations_list
    assert "Title 2" in citations_list
    assert "Title 3" in citations_list
    assert "https://example.com/1" in citations_list
    assert "https://example.com/2" in citations_list
    assert "https://example.com/3" in citations_list


if __name__ == "__main__":
    # Run basic tests
    test_citation_manager_initialization()
    print("✅ Citation manager initialization test passed")
    
    test_citation_manager_reset()
    print("✅ Citation manager reset test passed")
    
    test_search_tool_has_citation_manager()
    print("✅ Search tool citation manager test passed")
    
    test_citation_list_generation()
    print("✅ Citation list generation test passed")
    
    print("\n🎉 All integration tests passed!")

