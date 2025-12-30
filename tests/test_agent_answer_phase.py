"""Test script for enhanced agent answer phase with reasoning and citation links."""

import asyncio
import logging
from src.agents.react_agent import ReActAgent
from src.config.agent_config import AgentConfig
from src.models.factory import get_model_wrapper
from src.config.model_config import ModelConfig, ModelProvider
from src.search.global_citation_manager import GlobalCitationManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agent_answer_with_reasoning():
    """Test agent answer phase with reasoning display and citation links."""
    
    # Create agent configuration
    config = AgentConfig(
        max_iterations=3,
        max_execution_time=60,
        verbose=True
    )
    
    # Create models (using mock or real models)
    try:
        # Try to create real models if configured
        function_call_config = ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-chat",
            temperature=0.7
        )
        function_call_llm = get_model_wrapper(config=function_call_config)
        
        answer_config = ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-reasoner",  # DeepSeek-R1 for reasoning
            temperature=0.7
        )
        answer_llm = get_model_wrapper(config=answer_config)
        
        logger.info("✅ 使用真实模型进行测试")
    except Exception as e:
        logger.warning(f"无法创建真实模型: {e}")
        logger.info("使用模拟模式测试")
        return
    
    # Create citation manager
    citation_manager = GlobalCitationManager()
    
    # Create agent
    agent = ReActAgent(
        function_call_llm=function_call_llm,
        answer_llm=answer_llm,
        config=config,
        citation_manager=citation_manager
    )
    
    # Test query
    test_query = "2025年最热门的AI开源项目有哪些？"
    
    logger.info(f"\n{'='*60}")
    logger.info(f"测试查询: {test_query}")
    logger.info(f"{'='*60}\n")
    
    # Run agent with streaming
    try:
        step_count = 0
        reasoning_steps = []
        final_answer = ""
        
        async for step in agent.run_async(test_query):
            step_count += 1
            
            if step.type == "reasoning":
                reasoning_steps.append(step.content)
                logger.info(f"\n[步骤 {step_count}] 推理过程:")
                logger.info(f"  {step.content[:200]}...")
                
                # Check if this is answer phase reasoning
                if step.metadata and step.metadata.get("reasoning_type") == "answer_phase":
                    logger.info("  ✅ 检测到 answer_llm 推理内容")
                    
            elif step.type == "final":
                final_answer += step.content
                
                # Check for citation links
                if "[" in step.content and "](" in step.content:
                    logger.info(f"\n[步骤 {step_count}] 检测到引用链接:")
                    logger.info(f"  {step.content}")
                    
            elif step.type == "action":
                logger.info(f"\n[步骤 {step_count}] 工具调用:")
                logger.info(f"  {step.content[:100]}...")
                
            elif step.type == "observation":
                logger.info(f"\n[步骤 {step_count}] 工具结果:")
                logger.info(f"  {step.content[:100]}...")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"测试完成统计:")
        logger.info(f"  总步骤数: {step_count}")
        logger.info(f"  推理步骤数: {len(reasoning_steps)}")
        logger.info(f"  最终回答长度: {len(final_answer)}")
        
        # Check for answer phase reasoning
        answer_phase_reasoning = [
            step for step in reasoning_steps 
            if "answer_phase" in str(step) or "answer_llm" in str(step).lower()
        ]
        
        if answer_phase_reasoning:
            logger.info(f"  ✅ 成功展示 answer_llm 推理过程")
        else:
            logger.warning(f"  ⚠️ 未检测到 answer_llm 推理过程")
        
        # Check for citation links
        import re
        citation_links = re.findall(r'\[\d+\]\([^)]+\)', final_answer)
        if citation_links:
            logger.info(f"  ✅ 成功转换 {len(citation_links)} 个引用为链接")
            logger.info(f"  示例: {citation_links[0] if citation_links else 'N/A'}")
        else:
            logger.warning(f"  ⚠️ 未检测到引用链接")
        
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)


async def test_citation_conversion():
    """Test citation conversion logic independently."""
    from src.search.citation_processor import CitationProcessor
    from src.search.models import SearchResponse, SearchResult
    
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
        "根据研究[1]，AI技术发展迅速。",
        "多项研究[1][2]表明这一点。",
        "参考文献[15]提供了详细信息。",
        "这是一个没有引用的句子。",
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        logger.info(f"测试用例 {i}:")
        logger.info(f"  原文: {test_text}")
        
        converted = processor.convert_citations(test_text)
        logger.info(f"  转换后: {converted}")
        
        # Check if conversion happened
        if "[" in converted and "](" in converted:
            logger.info("  ✅ 成功转换引用为链接")
        elif "[" in test_text and "]" in test_text:
            logger.warning("  ⚠️ 包含引用但未成功转换")
        else:
            logger.info("  ℹ️ 无引用需要转换")
        
        logger.info("")


async def main():
    """Run all tests."""
    logger.info("\n" + "="*60)
    logger.info("开始测试增强的 Agent 回答阶段功能")
    logger.info("="*60 + "\n")
    
    # Test citation conversion first (independent)
    await test_citation_conversion()
    
    # Test full agent flow (requires real models)
    await test_agent_answer_with_reasoning()
    
    logger.info("\n" + "="*60)
    logger.info("所有测试完成")
    logger.info("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

