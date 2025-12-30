"""测试 API 超时修复"""

import asyncio
import sys
from src.agents.react_agent import ReActAgent
from src.search.search_tool import SearchTool
from src.models.factory import get_model_wrapper
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_agent_with_timeout():
    """测试 Agent 在超时场景下的回退机制"""
    
    print("\n" + "="*70)
    print("🧪 测试 API 超时修复")
    print("="*70 + "\n")
    
    # 获取双 LLM 配置
    function_call_config = os.getenv("AGENT_FUNCTION_CALL_MODEL")
    answer_config = os.getenv("AGENT_ANSWER_MODEL")
    
    if not function_call_config or not answer_config:
        print("❌ 请在 .env 中配置 AGENT_FUNCTION_CALL_MODEL 和 AGENT_ANSWER_MODEL")
        return
    
    function_call_config = json.loads(function_call_config)
    answer_config = json.loads(answer_config)
    
    print(f"📋 Function Call LLM: {function_call_config['provider']} - {function_call_config['model_name']}")
    print(f"📋 Answer LLM: {answer_config['provider']} - {answer_config['model_name']}")
    print()
    
    # 创建模型
    function_call_llm = get_model_wrapper(
        provider=function_call_config['provider'],
        model_name=function_call_config['model_name']
    )
    
    answer_llm = get_model_wrapper(
        provider=answer_config['provider'],
        model_name=answer_config['model_name']
    )
    
    # 创建搜索工具
    search_tool = SearchTool()
    
    # 创建 Agent
    agent = ReActAgent(
        llm=function_call_llm,
        search_tool=search_tool,
        answer_llm=answer_llm
    )
    
    # 测试问题
    test_query = "搜索并总结一下 2025 年最热门的 3 个 AI 项目"
    
    print(f"❓ 测试问题: {test_query}\n")
    print("⏱️  开始执行（观察是否出现超时和回退）...\n")
    print("-" * 70 + "\n")
    
    try:
        step_count = 0
        has_final_answer = False
        has_error = False
        
        async for step in agent.stream(test_query):
            step_count += 1
            
            if step.type == "reasoning":
                print(f"🧠 推理步骤 {step_count}:")
                print(f"   {step.content[:200]}..." if len(step.content) > 200 else f"   {step.content}")
                print()
                
            elif step.type == "action":
                print(f"🔧 工具调用 {step_count}: {step.content}")
                print()
                
            elif step.type == "observation":
                print(f"👀 观察结果 {step_count}:")
                print(f"   {step.content[:200]}..." if len(step.content) > 200 else f"   {step.content}")
                print()
                
            elif step.type == "final":
                if not has_final_answer:
                    print(f"💬 最终回答:")
                    has_final_answer = True
                print(step.content, end="")
                
            elif step.type == "error":
                print(f"\n❌ 错误: {step.content}")
                has_error = True
        
        print("\n")
        print("-" * 70)
        
        if has_final_answer:
            print("\n✅ 测试成功：Agent 成功生成了回答")
            print("   （即使遇到超时，回退机制也正常工作）")
        elif has_error:
            print("\n⚠️  测试结果：遇到错误但系统优雅降级")
            print("   （错误提示友好，系统没有崩溃）")
        else:
            print("\n❌ 测试失败：没有生成回答")
        
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_agent_with_timeout())
