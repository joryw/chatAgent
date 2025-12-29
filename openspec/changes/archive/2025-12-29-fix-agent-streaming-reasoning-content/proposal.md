# Change: 修复 Agent 流式调用中 function call 时缺少 reasoning_content 的问题

## Why

在 Agent 模式下使用 DeepSeek 模型进行流式调用时，当 Agent 决定调用工具（function call）时，DeepSeek API 要求 assistant message 必须包含 `reasoning_content` 字段。当前实现在某些场景下（特别是 LangGraph 流式调用和消息历史处理）未能正确添加该字段，导致 API 返回 400 错误：

```
Missing `reasoning_content` field in the assistant message at message index 1. 
For more information, please refer to https://api-docs.deepseek.com/guides/thinking_mode#tool-calls
```

这个问题会导致：
1. Agent 流式执行失败，无法完成工具调用
2. 用户体验中断，需要手动重试或切换到 Chat 模式
3. 错误信息不够友好，用户难以理解问题原因

## What Changes

### 修复内容
- **增强消息历史处理**: 在 LangGraph 流式调用时，确保消息历史中的所有 assistant message（包含 tool_calls）都正确添加 `reasoning_content` 字段
- **改进错误处理**: 当检测到 `reasoning_content` 相关错误时，自动修复并重试，而不是直接失败
- **完善日志记录**: 添加详细的调试日志，帮助定位问题
- **统一消息处理逻辑**: 确保所有调用路径（同步、异步、流式）都使用统一的 `reasoning_content` 处理逻辑

### 技术改进
- 在 `DeepSeekWrapper.get_langchain_llm()` 中增强消息处理逻辑
- 在 LangGraph 的流式调用路径中拦截并修复消息格式
- 添加消息验证和自动修复机制
- 改进错误恢复策略

## Impact

### 受影响的 specs
- **model-invocation**: 需要更新规范，明确要求在处理 DeepSeek 模型的 tool_calls 时必须包含 `reasoning_content` 字段

### 受影响的代码
- `src/models/deepseek_wrapper.py` - 增强消息处理逻辑，确保所有 assistant message 都包含 `reasoning_content`
- `src/agents/react_agent.py` - 可能需要添加消息格式验证（如果需要）
- 可能需要更新错误处理文档

### 用户体验改进
- Agent 流式调用更加稳定，减少因格式错误导致的失败
- 错误恢复更智能，自动修复常见问题
- 更好的错误提示和日志记录

## Breaking Changes

无破坏性变更。此修复仅增强现有功能，不改变 API 或行为接口。

