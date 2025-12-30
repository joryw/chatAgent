"""Simple test for citation conversion functionality."""

import logging
from src.search.citation_processor import CitationProcessor
from src.search.models import SearchResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_citation_conversion():
    """Test citation conversion logic."""
    
    logger.info("\n" + "="*60)
    logger.info("测试引用转换功能")
    logger.info("="*60 + "\n")
    
    # Create mock citation map
    citation_map = {
        1: {
            'url': 'https://example.com/article1',
            'title': 'Article 1',
            'domain': 'example.com'
        },
        2: {
            'url': 'https://example.com/article2',
            'title': 'Article 2',
            'domain': 'example.com'
        },
        15: {
            'url': 'https://example.com/article15',
            'title': 'Article 15',
            'domain': 'example.com'
        }
    }
    
    # Create citation processor
    processor = CitationProcessor(
        SearchResponse(query="test", results=[], total_results=0, search_time=0.0),
        offset=0
    )
    processor.citation_map = citation_map
    
    # Test cases
    test_cases = [
        ("根据研究[1]，AI技术发展迅速。", "单个引用"),
        ("多项研究[1][2]表明这一点。", "连续多个引用"),
        ("参考文献[15]提供了详细信息。", "两位数引用"),
        ("这是一个没有引用的句子。", "无引用"),
        ("研究[1]和[2]都表明[15]这一点。", "分散的多个引用"),
    ]
    
    all_passed = True
    
    for i, (test_text, description) in enumerate(test_cases, 1):
        logger.info(f"测试用例 {i}: {description}")
        logger.info(f"  原文: {test_text}")
        
        try:
            converted = processor.convert_citations(test_text)
            logger.info(f"  转换后: {converted}")
            
            # Check if conversion happened correctly
            import re
            original_citations = re.findall(r'\[(\d+)\]', test_text)
            # Note: CitationProcessor uses [[num]](url) format (double brackets)
            converted_links = re.findall(r'\[\[(\d+)\]\]\([^)]+\)', converted)
            
            if original_citations:
                if len(converted_links) == len(original_citations):
                    logger.info(f"  ✅ 成功转换 {len(converted_links)} 个引用为链接")
                    
                    # Verify each citation was converted (double bracket format)
                    for citation_num in original_citations:
                        num = int(citation_num)
                        if f"[[{num}]]({citation_map[num]['url']})" in converted:
                            logger.info(f"    ✅ 引用 [{num}] 正确转换为 [[{num}]](url)")
                        else:
                            logger.error(f"    ❌ 引用 [{num}] 转换失败")
                            all_passed = False
                else:
                    logger.warning(f"  ⚠️ 引用数量不匹配: 原始 {len(original_citations)}, 转换后 {len(converted_links)}")
                    all_passed = False
            else:
                if "[" not in converted or "](" not in converted:
                    logger.info("  ✅ 无引用，正确保持原文")
                else:
                    logger.warning("  ⚠️ 不应该有引用链接")
                    all_passed = False
                    
        except Exception as e:
            logger.error(f"  ❌ 测试失败: {e}")
            all_passed = False
        
        logger.info("")
    
    logger.info("="*60)
    if all_passed:
        logger.info("✅ 所有测试通过")
    else:
        logger.error("❌ 部分测试失败")
    logger.info("="*60 + "\n")
    
    return all_passed


def test_streaming_citation_conversion():
    """Test citation conversion in streaming mode (simulated)."""
    
    logger.info("\n" + "="*60)
    logger.info("测试流式输出中的引用转换")
    logger.info("="*60 + "\n")
    
    # Simulate streaming tokens
    test_sentence = "根据研究[1]，AI技术发展迅速[2]。"
    tokens = list(test_sentence)  # Simulate character-by-character streaming
    
    # Create citation map
    citation_map = {
        1: {'url': 'https://example.com/1', 'title': 'Article 1', 'domain': 'example.com'},
        2: {'url': 'https://example.com/2', 'title': 'Article 2', 'domain': 'example.com'},
    }
    
    # Simulate streaming
    full_content = ""
    output = ""
    
    logger.info("模拟流式输出:")
    logger.info(f"  原始句子: {test_sentence}\n")
    
    for i, token in enumerate(tokens):
        full_content += token
        
        # Check if we just completed a citation pattern
        import re
        if token == ']':
            # Look back for [num] pattern
            match = re.search(r'\[(\d+)\]$', full_content)
            if match:
                citation_num = int(match.group(1))
                if citation_num in citation_map:
                    url = citation_map[citation_num]['url']
                    # Append URL to create markdown link
                    token = f"]({url})"
                    logger.info(f"  位置 {i}: 检测到引用 [{citation_num}]，添加 URL")
        
        output += token
    
    logger.info(f"\n  转换后: {output}\n")
    
    # Verify conversion
    import re
    links = re.findall(r'\[(\d+)\]\([^)]+\)', output)
    
    if len(links) == 2:
        logger.info(f"✅ 成功在流式输出中转换 {len(links)} 个引用")
        return True
    else:
        logger.error(f"❌ 流式转换失败，期望 2 个链接，实际 {len(links)} 个")
        return False


if __name__ == "__main__":
    logger.info("\n" + "="*60)
    logger.info("开始测试引用转换功能")
    logger.info("="*60 + "\n")
    
    # Test basic conversion
    test1_passed = test_citation_conversion()
    
    # Test streaming conversion
    test2_passed = test_streaming_citation_conversion()
    
    logger.info("\n" + "="*60)
    if test1_passed and test2_passed:
        logger.info("✅ 所有测试通过")
    else:
        logger.error("❌ 部分测试失败")
    logger.info("="*60 + "\n")

