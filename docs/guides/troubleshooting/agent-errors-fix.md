---
title: Agent 模式错误修复总结
title_en: Agent Mode Errors Fix Summary
type: troubleshooting
created: 2024-12-28
updated: 2024-12-28
version: 1.0.0
tags: [agent, search_tool, deepseek, reasoning_content, bugfix]
lang: zh-CN
status: published
---

# Agent 模式错误修复总结

## 问题概述

在 Agent 模式使用过程中遇到两个主要错误：

1. **搜索工具错误**: `'SearchService' object has no attribute 'search_async'`
2. **DeepSeek API 错误**: `Missing reasoning_content field in the assistant message at message index 1`

## 问题 1: SearchService search_async 方法缺失

### 错误信息

```
搜索失败: 'SearchService' object has no attribute 'search_async'。请尝试重新搜索或基于已有知识回答。
```

### 问题原因

`SearchTool._arun` 方法调用了不存在的 `search_async` 方法。实际上 `SearchService` 只有 `search` 方法（已经是异步的），没有 `search_async` 方法。

### 解决方案

**文件**: `src/agents/tools/search_tool.py`

**修复前**:
```python
async def _arun(self, query: str) -> str:
    results = await self.search_service.search_async(query)  # ❌ 方法不存在
```

**修复后**:
```python
async def _arun(self, query: str) -> str:
    # SearchService.search is already async, use it directly
    search_response = await self.search_service.search(query)  # ✅ 使用正确的方法
    
    if not search_response or search_response.is_empty():
        return "未找到相关搜索结果..."
    
    # Extract results from SearchResponse
    results = search_response.results if search_response.results else []
    # ... 格式化结果
```

**同时修复了 `_run` 方法**:
- 添加了 `asyncio.run()` 来执行异步搜索
- 添加了错误处理，避免在异步上下文中调用同步方法

## 问题 2: DeepSeek reasoning_content 字段缺失（流式输出）

### 错误信息

```
Error code: 400 - {'error': {'message': 'Missing reasoning_content field in the assistant message at message index 1...'}}
```

### 问题原因

1. **流式输出路径**: LangGraph 在流式输出时可能直接调用 `astream` 方法，需要单独处理
2. **消息索引问题**: 错误提到 "message index 1"，可能是工具调用后的后续 assistant 消息
3. **上下文感知**: 某些 assistant 消息虽然没有直接的 `tool_calls`，但在工具调用流程中也需要 `reasoning_content`

### 解决方案

**文件**: `src/models/deepseek_wrapper.py`

#### 1. 改进消息处理逻辑

```python
def _add_reasoning_content_to_messages(self, messages):
    """Helper method to add reasoning_content to messages."""
    modified = []
    for i, msg in enumerate(messages):
        if isinstance(msg, dict):
            msg_copy = msg.copy()
            role = msg_copy.get("role")
            tool_calls = msg_copy.get("tool_calls")
            
            # 主要情况: assistant 消息有 tool_calls
            if role == "assistant" and tool_calls:
                if "reasoning_content" not in msg_copy:
                    reasoning = msg_copy.get("content", "") or "正在思考如何使用工具来回答这个问题..."
                    msg_copy["reasoning_content"] = reasoning
                    logger.info(f"✅ [消息索引 {i}] 添加 reasoning_content")
            
            # 次要情况: assistant 消息在工具调用流程中
            elif role == "assistant" and i > 0:
                prev_msg = messages[i-1]
                if isinstance(prev_msg, dict) and prev_msg.get("role") == "assistant" and prev_msg.get("tool_calls"):
                    if "reasoning_content" not in msg_copy:
                        reasoning = msg_copy.get("content", "") or "正在处理工具调用结果..."
                        msg_copy["reasoning_content"] = reasoning
                        logger.info(f"✅ [消息索引 {i}] 添加上下文 reasoning_content")
            
            modified.append(msg_copy)
    
    return modified
```

#### 2. 添加错误处理和重试

```python
def _wrap_client_create(self, original_create):
    def wrapped_create(*args, **create_kwargs):
        if "messages" in create_kwargs:
            create_kwargs["messages"] = self._add_reasoning_content_to_messages(
                create_kwargs["messages"]
            )
        
        try:
            return original_create(*args, **create_kwargs)
        except Exception as e:
            error_str = str(e)
            # 如果仍然遇到 reasoning_content 错误，尝试更激进的修复
            if "reasoning_content" in error_str.lower() and "messages" in create_kwargs:
                logger.warning(f"⚠️ 仍然遇到 reasoning_content 错误，尝试更激进的修复")
                # 修复所有 assistant 消息
                msgs = create_kwargs["messages"]
                for i, msg in enumerate(msgs):
                    if isinstance(msg, dict) and msg.get("role") == "assistant":
                        if "reasoning_content" not in msg:
                            msg["reasoning_content"] = msg.get("content", "") or "正在思考中..."
                            logger.info(f"✅ [错误修复] 消息索引 {i} 强制添加 reasoning_content")
                # 重试
                return original_create(*args, **create_kwargs)
            raise
    
    return wrapped_create
```

#### 3. 确保流式输出也被处理

```python
async def astream(self, input, config=None, **kwargs):
    """Override astream to add reasoning_content before streaming API call."""
    original_create = self.client.create
    wrapped_create = self._wrap_client_create(original_create)
    
    self.client.create = wrapped_create
    try:
        async for chunk in super().astream(input, config=config, **kwargs):
            yield chunk
    finally:
        self.client.create = original_create
```

## 修复的文件

1. **`src/agents/tools/search_tool.py`**
   - 修复 `_arun` 方法，使用正确的 `search` 方法
   - 改进 `_run` 方法，添加异步支持

2. **`src/models/deepseek_wrapper.py`**
   - 改进 `_add_reasoning_content_to_messages` 方法，支持上下文感知
   - 添加错误处理和重试逻辑
   - 确保流式输出也被正确处理

## 验证步骤

1. **测试搜索工具**:
   ```bash
   # 启动应用
   chainlit run app.py -w
   ```
   - 切换到 Agent 模式
   - 发送需要搜索的问题
   - 应该能正常调用搜索工具，不再出现 `search_async` 错误

2. **测试 DeepSeek reasoning_content**:
   - 确保使用 DeepSeek 模型
   - 发送需要工具调用的问题
   - 应该能正常完成，不再出现 `reasoning_content` 错误
   - 查看日志，应该看到 "✅ 添加 reasoning_content" 的消息

## 技术细节

### 搜索工具修复

- **问题**: `SearchService` 只有异步的 `search` 方法，没有 `search_async`
- **解决**: 直接使用 `search` 方法，并正确处理 `SearchResponse` 对象
- **同步支持**: `_run` 方法使用 `asyncio.run()` 执行异步搜索

### DeepSeek reasoning_content 修复

- **多层拦截**: 
  - 方法层面: `_generate`, `_astream`, `astream`
  - 客户端层面: `create`, `stream`
- **上下文感知**: 不仅处理有 `tool_calls` 的消息，还处理工具调用流程中的后续消息
- **错误恢复**: 如果第一次修复失败，尝试更激进的修复（修复所有 assistant 消息）

## 相关文档

- [DeepSeek reasoning_content 修复](./deepseek-reasoning-content-fix.md)
- [Agent 流式输出修复](./agent-streaming-fix.md)
- [Agent Mode Usage Guide](../agent-mode.md)

---

**最后更新**: 2024-12-28  
**版本**: 1.0.0  
**状态**: ✅ 已修复

