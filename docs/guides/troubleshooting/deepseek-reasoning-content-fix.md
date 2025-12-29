---
title: DeepSeek reasoning_content 字段修复
title_en: DeepSeek reasoning_content Field Fix
type: troubleshooting
created: 2024-12-28
updated: 2024-12-28
version: 1.0.0
tags: [deepseek, reasoning_content, tool_calls, bugfix]
lang: zh-CN
status: published
---

# DeepSeek reasoning_content 字段修复

## 问题描述

在使用 DeepSeek 模型进行 Agent 模式工具调用时，遇到以下错误：

```
Error code: 400 - {'error': {'message': 'Missing reasoning_content field in the assistant message at message index 1. For more information, please refer to https://api-docs.deepseek.com/guides/thinking_mode#tool-calls', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
```

## 问题原因

DeepSeek API 在使用工具调用（tool calls）时，要求 assistant 消息必须包含 `reasoning_content` 字段。这是 DeepSeek 的特殊要求，用于支持其"思考模式"（thinking mode）。

当 LangGraph Agent 创建包含工具调用的 assistant 消息时，LangChain 的 `ChatOpenAI` 不会自动添加 `reasoning_content` 字段，导致 API 调用失败。

## 解决方案

在 `DeepSeekWrapper.get_langchain_llm()` 方法中，包装 LangChain 的客户端 `create` 方法，在调用 API 之前自动为包含工具调用的 assistant 消息添加 `reasoning_content` 字段。

### 实现细节

**文件**: `src/models/deepseek_wrapper.py`

**修复策略**: 创建一个自定义的 `ChatOpenAI` 子类，重写 `_generate` 方法，在调用 API 之前拦截并修改消息。

**修复代码**:
```python
def get_langchain_llm(self):
    """Get LangChain compatible LLM instance with DeepSeek reasoning_content support."""
    # Create a custom ChatOpenAI subclass that handles reasoning_content
    class DeepSeekChatOpenAI(ChatOpenAI):
        """Custom ChatOpenAI that adds reasoning_content for DeepSeek API."""
        
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            """Override _generate to add reasoning_content before API call."""
            # Intercept the API call at the client level
            original_create = self.client.create
            
            def wrapped_create(*args, **create_kwargs):
                """Wrapper that adds reasoning_content to messages."""
                if "messages" in create_kwargs:
                    msgs = create_kwargs["messages"]
                    modified = []
                    
                    for i, msg in enumerate(msgs):
                        if isinstance(msg, dict):
                            msg_copy = msg.copy()
                            role = msg_copy.get("role")
                            tool_calls = msg_copy.get("tool_calls")
                            
                            # Add reasoning_content for assistant messages with tool_calls
                            if role == "assistant" and tool_calls:
                                if "reasoning_content" not in msg_copy:
                                    reasoning = msg_copy.get("content", "")
                                    if not reasoning or reasoning.strip() == "":
                                        reasoning = "正在思考如何使用工具来回答这个问题..."
                                    msg_copy["reasoning_content"] = reasoning
                                    logger.info(f"✅ [消息索引 {i}] 添加 reasoning_content")
                            
                            modified.append(msg_copy)
                        else:
                            modified.append(msg)
                    
                    create_kwargs["messages"] = modified
                
                return original_create(*args, **create_kwargs)
            
            # Replace create method temporarily
            self.client.create = wrapped_create
            try:
                return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
            finally:
                # Restore original
                self.client.create = original_create
    
    # Create new instance with same configuration
    wrapped_model = DeepSeekChatOpenAI(...)
    
    # Also wrap proactively for additional safety
    wrapped_model.client.create = proactive_wrapped_create
    
    return wrapped_model
```

### 工作原理

1. **创建自定义 ChatOpenAI 子类**: 继承 LangChain 的 `ChatOpenAI`，重写多个方法
2. **同步调用拦截**: 重写 `_generate` 方法，在调用父类方法之前临时包装客户端的 `create` 方法
3. **异步流式拦截**: 重写 `_astream` 和 `astream` 方法，确保流式输出也能正确处理
4. **检查消息格式**: 遍历所有消息，查找包含 `tool_calls` 的 assistant 消息
5. **添加 reasoning_content**: 如果缺少 `reasoning_content` 字段，使用消息的 `content` 作为 reasoning，如果没有 content，使用默认文本
6. **多层保护**: 
   - 在 `_generate`、`_astream`、`astream` 中临时包装
   - 在客户端层面永久包装 `create` 和 `stream` 方法
   - 确保所有调用路径（同步、异步、流式）都被处理
7. **转发请求**: 将修改后的消息传递给原始 API 调用

### 流式输出处理

LangGraph 在流式输出时可能直接调用 `astream` 方法，因此需要单独处理：

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

## 验证步骤

1. **启动应用**:
   ```bash
   chainlit run app.py -w
   ```

2. **切换到 Agent 模式**:
   - 点击 ⚙️ 设置图标
   - 选择"对话模式"为 **agent**
   - 确保使用 DeepSeek 模型

3. **测试工具调用**:
   - 发送需要搜索的问题，例如："帮我找一下腾讯的新闻"
   - Agent 应该能够正常调用搜索工具，不再出现 `reasoning_content` 错误

4. **检查日志**:
   - 查看控制台日志，应该看到 "✅ 添加 reasoning_content 到 assistant message" 的调试信息

## 相关文档

- [DeepSeek API Documentation - Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode#tool-calls)
- [Agent Mode Usage Guide](../agent-mode.md)
- [LangChain Migration Guide](./langchain-migration.md)

## 技术细节

### DeepSeek API 要求

根据 DeepSeek API 文档，当 assistant 消息包含 `tool_calls` 时，必须同时包含 `reasoning_content` 字段：

```json
{
  "role": "assistant",
  "content": "...",
  "reasoning_content": "正在思考如何使用工具...",
  "tool_calls": [...]
}
```

### LangChain 消息格式

LangChain 在调用 OpenAI 兼容 API 时，会将消息转换为以下格式：

```python
{
  "role": "assistant",
  "content": "...",
  "tool_calls": [...]
}
```

我们的修复在 API 调用之前添加缺失的 `reasoning_content` 字段。

## 流式输出支持

除了同步的 `_generate` 方法，修复还支持流式输出：

1. **`_astream` 方法**: 重写以支持异步流式输出
2. **`astream` 方法**: 重写以支持 LangGraph 的流式调用
3. **`client.stream` 方法**: 包装客户端的同步流式方法

这确保了无论是同步、异步还是流式调用，都能正确处理 `reasoning_content` 字段。

## 注意事项

1. **仅影响 DeepSeek**: 此修复仅适用于 DeepSeek 模型，其他模型（OpenAI、Anthropic）不受影响
2. **默认 reasoning**: 如果消息没有 `content`，使用默认文本 "正在思考如何使用工具来回答这个问题..."
3. **性能影响**: 包装方法会轻微增加调用开销，但影响可以忽略不计
4. **流式输出**: 修复同时支持同步和异步流式输出，确保所有调用路径都被处理

## 故障排除

如果问题仍然存在：

1. **检查模型配置**: 确保使用的是 DeepSeek 模型
2. **查看日志**: 检查是否有 "✅ 添加 reasoning_content" 的日志
3. **验证 API 密钥**: 确保 DeepSeek API 密钥配置正确
4. **检查消息格式**: 查看实际发送给 API 的消息格式

---

**最后更新**: 2024-12-28  
**版本**: 1.0.0  
**状态**: ✅ 已修复

