#!/usr/bin/env python3
"""Test script to verify SearchResponse initialization fix."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.search.models import SearchResponse, SearchResult
from src.search.citation_processor import CitationProcessor


def test_searchresponse_creation():
    """Test that SearchResponse can be created with all required parameters."""
    print("🧪 测试 SearchResponse 创建...")
    
    try:
        # Create SearchResponse with all required parameters
        response = SearchResponse(
            query="test query",
            results=[],
            total_results=0,
            search_time=0.0
        )
        print("✅ SearchResponse 创建成功（包含所有必需参数）")
        return True
    except TypeError as e:
        print(f"❌ SearchResponse 创建失败: {e}")
        return False


def test_citation_processor_with_dummy_response():
    """Test CitationProcessor can be created with dummy SearchResponse."""
    print("\n🧪 测试 CitationProcessor 使用虚拟 SearchResponse...")
    
    try:
        # This is how it's used in react_agent.py
        citation_processor = CitationProcessor(
            SearchResponse(query="", results=[], total_results=0, search_time=0.0), 
            offset=0
        )
        
        # Manually set citation map (as done in react_agent.py)
        citation_processor.citation_map = {
            1: {'url': 'https://example.com/1', 'title': 'Test 1', 'domain': 'example.com'},
            2: {'url': 'https://example.com/2', 'title': 'Test 2', 'domain': 'example.com'},
        }
        
        print("✅ CitationProcessor 创建成功")
        
        # Test citation conversion
        test_text = "这是一个测试 [1] 和另一个引用 [2]"
        converted = citation_processor.convert_citations(test_text)
        
        if "[[1]]" in converted and "[[2]]" in converted:
            print("✅ 引用转换功能正常")
            return True
        else:
            print(f"❌ 引用转换失败: {converted}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_citation_processor_with_results():
    """Test CitationProcessor with actual search results."""
    print("\n🧪 测试 CitationProcessor 使用真实搜索结果...")
    
    try:
        # Create real search results
        results = [
            SearchResult(
                title="Test Result 1",
                url="https://example.com/1",
                content="This is test content 1"
            ),
            SearchResult(
                title="Test Result 2",
                url="https://example.com/2",
                content="This is test content 2"
            )
        ]
        
        response = SearchResponse(
            query="test query",
            results=results,
            total_results=2,
            search_time=0.5
        )
        
        citation_processor = CitationProcessor(response, offset=0)
        
        # Test with citation
        test_text = "这是引用 [1] 和 [2]"
        converted = citation_processor.convert_citations(test_text)
        
        if "[[1]]" in converted and "[[2]]" in converted:
            print("✅ 真实搜索结果处理正常")
            
            # Test citation list generation
            citations_list = citation_processor.get_citations_list(test_text)
            if "Test Result 1" in citations_list and "Test Result 2" in citations_list:
                print("✅ 引用列表生成正常")
                return True
            else:
                print(f"❌ 引用列表生成失败: {citations_list}")
                return False
        else:
            print(f"❌ 引用转换失败: {converted}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("SearchResponse 初始化修复验证")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Basic SearchResponse creation
    if not test_searchresponse_creation():
        all_passed = False
    
    # Test 2: CitationProcessor with dummy response
    if not test_citation_processor_with_dummy_response():
        all_passed = False
    
    # Test 3: CitationProcessor with real results
    if not test_citation_processor_with_results():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分测试失败")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

