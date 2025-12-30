#!/usr/bin/env python3
"""测试 reasoning_content 修复功能。

这个脚本直接测试消息处理逻辑，不依赖完整的模块导入。
"""

import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模拟 BaseMessage 和 AIMessage（如果 langchain 不可用）
try:
    from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
except ImportError:
    class BaseMessage:
        pass
    class AIMessage(BaseMessage):
        def __init__(self, content="", tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls or []
    class HumanMessage(BaseMessage):
        def __init__(self, content=""):
            self.content = content


def _add_reasoning_content_to_messages_helper(messages):
    """Helper function to add reasoning_content to messages.
    
    这是从 deepseek_wrapper.py 复制的函数，用于独立测试。
    """
    modified = []
    for i, msg in enumerate(messages):
        # Handle dict format (most common in API calls)
        if isinstance(msg, dict):
            msg_copy = msg.copy()
            role = msg_copy.get("role")
            tool_calls = msg_copy.get("tool_calls")
            
            # Log message details for debugging
            logger.debug(f"处理消息索引 {i}: role={role}, has_tool_calls={bool(tool_calls)}, has_reasoning={bool(msg_copy.get('reasoning_content'))}")
            
            # CRITICAL: Add reasoning_content for ALL assistant messages with tool_calls
            # DeepSeek API requires this field when tool_calls are present
            if role == "assistant" and tool_calls:
                if "reasoning_content" not in msg_copy:
                    reasoning = msg_copy.get("content", "")
                    if not reasoning or reasoning.strip() == "":
                        reasoning = "正在思考如何使用工具来回答这个问题..."
                    msg_copy["reasoning_content"] = reasoning
                    logger.info(f"✅ [消息索引 {i}] 添加 reasoning_content (工具调用: {len(tool_calls)} 个)")
                else:
                    logger.debug(f"消息索引 {i} 已有 reasoning_content")
            
            # Also check for assistant messages in tool-calling context
            # Sometimes DeepSeek requires reasoning_content even without explicit tool_calls
            # if it's part of a tool-calling conversation
            elif role == "assistant" and i > 0:
                # Check if previous messages indicate tool-calling context
                prev_msg = messages[i-1] if i > 0 else None
                if isinstance(prev_msg, dict) and prev_msg.get("role") == "assistant" and prev_msg.get("tool_calls"):
                    # This might be a follow-up assistant message in tool-calling flow
                    if "reasoning_content" not in msg_copy:
                        reasoning = msg_copy.get("content", "")
                        if not reasoning or reasoning.strip() == "":
                            reasoning = "正在处理工具调用结果..."
                        msg_copy["reasoning_content"] = reasoning
                        logger.info(f"✅ [消息索引 {i}] 添加上下文 reasoning_content (工具调用流程)")
            
            modified.append(msg_copy)
        
        # Handle BaseMessage format (from LangChain)
        elif isinstance(msg, BaseMessage):
            # Convert BaseMessage to dict for processing
            msg_dict = {}
            if hasattr(msg, 'role'):
                msg_dict['role'] = msg.role
            elif isinstance(msg, AIMessage):
                msg_dict['role'] = 'assistant'
            else:
                msg_dict['role'] = getattr(msg, 'type', 'user')
            
            if hasattr(msg, 'content'):
                msg_dict['content'] = msg.content
            
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                msg_dict['tool_calls'] = msg.tool_calls
            
            # Process the converted dict
            role = msg_dict.get("role")
            tool_calls = msg_dict.get("tool_calls")
            
            if role == "assistant" and tool_calls:
                if "reasoning_content" not in msg_dict:
                    reasoning = msg_dict.get("content", "")
                    if not reasoning or reasoning.strip() == "":
                        reasoning = "正在思考如何使用工具来回答这个问题..."
                    msg_dict["reasoning_content"] = reasoning
                    logger.info(f"✅ [消息索引 {i}] BaseMessage 格式添加 reasoning_content (工具调用: {len(tool_calls)} 个)")
            
            # For BaseMessage, we convert to dict format for API compatibility
            modified.append(msg_dict)
        else:
            # Unknown format, pass through (but log warning)
            logger.warning(f"⚠️ 未知消息格式在索引 {i}: {type(msg)}")
            modified.append(msg)
    
    return modified


def test_dict_format_with_tool_calls():
    """测试 dict 格式的消息，包含 tool_calls"""
    print("=" * 60)
    print("测试 1: dict 格式消息，包含 tool_calls")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "搜索一下 Python"},
        {
            "role": "assistant",
            "content": "我需要搜索 Python 相关信息",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "web_search", "arguments": '{"query": "Python"}'}
                }
            ]
        }
    ]
    
    result = _add_reasoning_content_to_messages_helper(messages)
    
    # 检查结果
    assert len(result) == 2, f"期望 2 条消息，实际 {len(result)}"
    assert result[0]["role"] == "user", "第一条消息应该是 user"
    
    assistant_msg = result[1]
    assert assistant_msg["role"] == "assistant", "第二条消息应该是 assistant"
    assert "tool_calls" in assistant_msg, "应该包含 tool_calls"
    assert "reasoning_content" in assistant_msg, "应该包含 reasoning_content"
    assert assistant_msg["reasoning_content"] == "我需要搜索 Python 相关信息", \
        f"reasoning_content 应该是消息内容，实际: {assistant_msg['reasoning_content']}"
    
    print("✅ 测试通过: dict 格式消息正确处理")
    print(f"   reasoning_content: {assistant_msg['reasoning_content']}")
    print()


def test_dict_format_empty_content():
    """测试 dict 格式的消息，tool_calls 但 content 为空"""
    print("=" * 60)
    print("测试 2: dict 格式消息，tool_calls 但 content 为空")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "搜索一下 Python"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "web_search", "arguments": '{"query": "Python"}'}
                }
            ]
        }
    ]
    
    result = _add_reasoning_content_to_messages_helper(messages)
    
    assistant_msg = result[1]
    assert "reasoning_content" in assistant_msg, "应该包含 reasoning_content"
    assert assistant_msg["reasoning_content"] == "正在思考如何使用工具来回答这个问题...", \
        f"应该使用默认 reasoning_content，实际: {assistant_msg['reasoning_content']}"
    
    print("✅ 测试通过: 空 content 时使用默认 reasoning_content")
    print(f"   reasoning_content: {assistant_msg['reasoning_content']}")
    print()


def test_basemessage_format():
    """测试 BaseMessage 格式的消息"""
    print("=" * 60)
    print("测试 3: BaseMessage 格式消息")
    print("=" * 60)
    
    messages = [
        HumanMessage(content="搜索一下 Python"),
        AIMessage(
            content="我需要搜索 Python 相关信息",
            tool_calls=[
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "web_search", "arguments": '{"query": "Python"}'}
                }
            ]
        )
    ]
    
    result = _add_reasoning_content_to_messages_helper(messages)
    
    # BaseMessage 会被转换为 dict
    assert len(result) == 2, f"期望 2 条消息，实际 {len(result)}"
    assert isinstance(result[0], dict), "应该转换为 dict"
    assert isinstance(result[1], dict), "应该转换为 dict"
    
    assistant_msg = result[1]
    assert assistant_msg["role"] == "assistant", "应该是 assistant"
    assert "tool_calls" in assistant_msg, "应该包含 tool_calls"
    assert "reasoning_content" in assistant_msg, "应该包含 reasoning_content"
    
    print("✅ 测试通过: BaseMessage 格式正确转换并处理")
    print(f"   reasoning_content: {assistant_msg['reasoning_content']}")
    print()


def test_message_history():
    """测试消息历史中的多个 assistant message"""
    print("=" * 60)
    print("测试 4: 消息历史中的多个 assistant message")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "搜索一下 Python"},
        {
            "role": "assistant",
            "content": "我需要搜索",
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "web_search", "arguments": '{"query": "Python"}'}}]
        },
        {"role": "tool", "content": "搜索结果..."},
        {
            "role": "assistant",
            "content": "基于搜索结果，我可以回答",
            "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "web_search", "arguments": '{"query": "Python tutorial"}'}}]
        }
    ]
    
    result = _add_reasoning_content_to_messages_helper(messages)
    
    # 检查所有 assistant message
    assistant_messages = [msg for msg in result if msg.get("role") == "assistant"]
    assert len(assistant_messages) == 2, f"应该有 2 个 assistant message，实际 {len(assistant_messages)}"
    
    for i, msg in enumerate(assistant_messages):
        assert "reasoning_content" in msg, f"第 {i+1} 个 assistant message 应该包含 reasoning_content"
        print(f"✅ Assistant message {i+1}: reasoning_content = {msg['reasoning_content']}")
    
    print("✅ 测试通过: 消息历史中的所有 assistant message 都正确处理")
    print()


def test_message_index_1():
    """测试消息索引 1 的情况（这是错误中提到的位置）"""
    print("=" * 60)
    print("测试 5: 消息索引 1（错误中提到的位置）")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "第一个问题"},
        {
            "role": "assistant",
            "content": "第一个回答",
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "web_search", "arguments": '{"query": "test"}'}}]
        },
        {"role": "user", "content": "第二个问题"},
        {
            "role": "assistant",  # 这是索引 3，但模拟索引 1 的情况
            "content": "第二个回答",
            "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "web_search", "arguments": '{"query": "test2"}'}}]
        }
    ]
    
    result = _add_reasoning_content_to_messages_helper(messages)
    
    # 检查索引 1 的消息（第二个消息）
    msg_at_index_1 = result[1]
    assert msg_at_index_1["role"] == "assistant", "索引 1 应该是 assistant"
    assert "tool_calls" in msg_at_index_1, "应该包含 tool_calls"
    assert "reasoning_content" in msg_at_index_1, "索引 1 的消息应该包含 reasoning_content"
    
    print(f"✅ 索引 1 的消息正确处理")
    print(f"   reasoning_content: {msg_at_index_1['reasoning_content']}")
    
    # 检查索引 3 的消息
    msg_at_index_3 = result[3]
    assert "reasoning_content" in msg_at_index_3, "索引 3 的消息也应该包含 reasoning_content"
    
    print(f"✅ 索引 3 的消息正确处理")
    print(f"   reasoning_content: {msg_at_index_3['reasoning_content']}")
    print("✅ 测试通过: 所有索引位置的 assistant message 都正确处理")
    print()


def test_existing_reasoning_content():
    """测试已经包含 reasoning_content 的消息"""
    print("=" * 60)
    print("测试 6: 已经包含 reasoning_content 的消息")
    print("=" * 60)
    
    messages = [
        {
            "role": "assistant",
            "content": "我需要搜索",
            "reasoning_content": "已有的思考内容",
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "web_search", "arguments": '{"query": "test"}'}}]
        }
    ]
    
    result = _add_reasoning_content_to_messages_helper(messages)
    
    assistant_msg = result[0]
    assert assistant_msg["reasoning_content"] == "已有的思考内容", \
        "应该保留已有的 reasoning_content"
    
    print("✅ 测试通过: 已有的 reasoning_content 被保留")
    print(f"   reasoning_content: {assistant_msg['reasoning_content']}")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试 reasoning_content 修复功能")
    print("=" * 60 + "\n")
    
    tests = [
        test_dict_format_with_tool_calls,
        test_dict_format_empty_content,
        test_basemessage_format,
        test_message_history,
        test_message_index_1,
        test_existing_reasoning_content,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {test_func.__name__}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {test_func.__name__}")
            print(f"   异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    import sys
    main()
