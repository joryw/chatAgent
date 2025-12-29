#!/usr/bin/env python3
"""验证实施的功能是否正确实现"""

import ast
import re
from pathlib import Path

def check_file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    return Path(file_path).exists()

def read_file(file_path: str) -> str:
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def check_reasoning_type_logic(file_path: str) -> tuple[bool, list[str]]:
    """检查 reasoning_type 逻辑是否正确实现"""
    content = read_file(file_path)
    issues = []
    
    # 检查是否跟踪 last_observation_time
    if 'last_observation_time' not in content:
        issues.append("❌ 未找到 last_observation_time 跟踪变量")
        return False, issues
    
    # 检查是否根据 last_observation_time 设置 reasoning_type
    if 'reasoning_type = "tool_selection"' not in content:
        issues.append("❌ 未找到 tool_selection 默认值设置")
        return False, issues
    
    if 'reasoning_type = "continue_decision"' not in content:
        issues.append("❌ 未找到 continue_decision 类型设置")
        return False, issues
    
    if 'if last_observation_time is not None:' not in content:
        issues.append("❌ 未找到基于 last_observation_time 的判断逻辑")
        return False, issues
    
    # 检查是否在 metadata 中设置 reasoning_type
    if '"reasoning_type": reasoning_type' not in content and "'reasoning_type': reasoning_type" not in content:
        issues.append("❌ 未找到在 metadata 中设置 reasoning_type")
        return False, issues
    
    return True, issues

def check_ui_display_logic(file_path: str) -> tuple[bool, list[str]]:
    """检查 UI 展示逻辑是否正确实现"""
    content = read_file(file_path)
    issues = []
    
    # 检查是否从 metadata 读取 reasoning_type
    if 'reasoning_type = step.metadata.get("reasoning_type"' not in content:
        issues.append("❌ 未找到从 metadata 读取 reasoning_type 的逻辑")
        return False, issues
    
    # 检查是否根据 reasoning_type 设置不同的 step 名称
    if '"💭 思考选择工具"' not in content:
        issues.append("❌ 未找到 '💭 思考选择工具' step 名称")
        return False, issues
    
    if '"💭 思考是否继续调用工具"' not in content:
        issues.append("❌ 未找到 '💭 思考是否继续调用工具' step 名称")
        return False, issues
    
    # 检查是否有更新逻辑
    if 'thinking_step.update()' not in content:
        issues.append("⚠️ 未找到 thinking_step.update() 调用（可能在某些 Chainlit 版本中不需要）")
    
    return True, issues

def check_streaming_output(file_path: str) -> tuple[bool, list[str]]:
    """检查流式输出是否正确实现"""
    content = read_file(file_path)
    issues = []
    
    # 检查 answer_llm 是否使用 astream
    if 'self.answer_llm.astream(' not in content:
        issues.append("❌ 未找到 answer_llm.astream() 调用")
        return False, issues
    
    # 检查是否使用 ainvoke（不应该使用）
    if 'self.answer_llm.ainvoke(' in content:
        issues.append("⚠️ 发现 answer_llm.ainvoke() 调用，应该使用 astream()")
        # 检查是否在 stream 方法中
        if 'async def stream' in content:
            stream_start = content.find('async def stream')
            ainvoke_pos = content.find('self.answer_llm.ainvoke(', stream_start)
            if ainvoke_pos != -1:
                issues.append("❌ 在 stream 方法中使用了 ainvoke，应该使用 astream")
                return False, issues
    
    # 检查是否 yield AgentStep
    if 'yield AgentStep(' not in content:
        issues.append("❌ 未找到 yield AgentStep 调用")
        return False, issues
    
    return True, issues

def main():
    """主验证函数"""
    print("=" * 60)
    print("验证实施的功能")
    print("=" * 60)
    
    react_agent_path = "src/agents/react_agent.py"
    app_path = "app.py"
    
    all_passed = True
    
    # 检查文件是否存在
    print("\n1. 检查文件是否存在...")
    if not check_file_exists(react_agent_path):
        print(f"❌ 文件不存在: {react_agent_path}")
        return False
    if not check_file_exists(app_path):
        print(f"❌ 文件不存在: {app_path}")
        return False
    print("✅ 所有文件存在")
    
    # 检查 reasoning_type 逻辑
    print("\n2. 检查 reasoning_type 逻辑...")
    passed, issues = check_reasoning_type_logic(react_agent_path)
    if passed:
        print("✅ reasoning_type 逻辑正确")
    else:
        print("❌ reasoning_type 逻辑有问题:")
        for issue in issues:
            print(f"   {issue}")
        all_passed = False
    
    # 检查 UI 展示逻辑
    print("\n3. 检查 UI 展示逻辑...")
    passed, issues = check_ui_display_logic(app_path)
    if passed:
        print("✅ UI 展示逻辑正确")
    else:
        print("❌ UI 展示逻辑有问题:")
        for issue in issues:
            print(f"   {issue}")
        all_passed = False
    
    # 检查流式输出
    print("\n4. 检查流式输出实现...")
    passed, issues = check_streaming_output(react_agent_path)
    if passed:
        print("✅ 流式输出实现正确")
    else:
        print("❌ 流式输出实现有问题:")
        for issue in issues:
            print(f"   {issue}")
        all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有验证通过！")
        print("\n下一步: 请按照 TESTING_GUIDE.md 进行手动测试")
    else:
        print("❌ 部分验证失败，请检查上述问题")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

