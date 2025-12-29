---
title: Agent 流式输出卡住问题修复
title_en: Agent Streaming Hang Fix
type: troubleshooting
created: 2024-12-28
updated: 2024-12-28
version: 1.0.0
tags: [agent, streaming, bugfix, langgraph]
lang: zh-CN
status: published
---

# Agent 流式输出卡住问题修复

## 问题描述

Agent 模式在执行时会卡在"思考中"状态，无法继续执行或返回结果。

## 问题原因

1. **LangGraph 事件流格式理解错误**: LangGraph 的 `astream()` 返回的事件格式与预期不同
2. **事件解析不完整**: 没有正确处理所有可能的事件类型
3. **最终答案提取失败**: 无法正确从消息流中提取最终答案
4. **UI 步骤管理问题**: `cl.Step` 没有正确关闭，导致 UI 一直显示"思考中"

## 解决方案

### 1. 改进事件流解析

**修复前**:
```python
async for event in self.agent_executor.astream(...):
    if "agent" in event:
        # 简单处理，可能遗漏某些情况
        pass
```

**修复后**:
```python
async for event in self.agent_executor.astream(...):
    # 更详细的事件解析
    if "agent" in event:
        agent_data = event["agent"]
        if isinstance(agent_data, dict) and "messages" in agent_data:
            messages = agent_data["messages"]
            # 区分工具调用和最终答案
            for msg in messages:
                if isinstance(msg, AIMessage):
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        # 工具调用
                    else:
                        # 推理或最终答案
```

### 2. 添加回退机制

如果流式输出失败，自动回退到非流式方法：

```python
try:
    # 尝试流式输出
    async for event in self.agent_executor.astream(...):
        ...
except Exception as e:
    # 回退到非流式方法
    result = await self.run(user_input)
    for step in result.steps:
        yield step
    yield AgentStep(type="final", content=result.final_answer)
```

### 3. 改进 UI 步骤管理

**修复前**:
```python
async with cl.Step(name="💭 思考中", type="tool") as thinking_step:
    thinking_step.output = step.content
# Step 可能一直打开
```

**修复后**:
```python
thinking_step = None
# ...
if step.type == "reasoning":
    if thinking_step is None:
        thinking_step = cl.Step(name="💭 思考中", type="tool")
        await thinking_step.__aenter__()
    thinking_step.output = step.content
# ...
elif step.type == "final":
    if thinking_step:
        await thinking_step.__aexit__(None, None, None)
        thinking_step = None
```

### 4. 添加超时处理

```python
try:
    async for step in agent.stream(user_message):
        # 处理步骤
        ...
except asyncio.TimeoutError:
    await cl.Message(
        content="⏱️ Agent 执行超时，请尝试简化问题或切换到 Chat 模式。",
        author="System",
    ).send()
```

## 修复的文件

1. **`src/agents/react_agent.py`**
   - 改进 `stream()` 方法的事件解析逻辑
   - 添加回退机制
   - 改进最终答案提取逻辑

2. **`app.py`**
   - 改进 `handle_agent_mode()` 的步骤管理
   - 添加超时处理
   - 确保所有步骤正确关闭

## 验证步骤

1. **启动应用**:
   ```bash
   chainlit run app.py -w
   ```

2. **测试 Agent 模式**:
   - 切换到 Agent 模式
   - 发送简单问题（如"你好"）
   - 观察是否正常完成，不再卡在"思考中"

3. **检查日志**:
   - 查看控制台日志，确认事件流正常
   - 确认最终答案正确提取

## 预期行为

修复后，Agent 模式应该：

1. ✅ 正常显示"思考中"步骤
2. ✅ 正确显示工具调用步骤
3. ✅ 正确显示工具结果
4. ✅ 最终返回答案，不再卡住
5. ✅ 如果流式输出失败，自动回退到非流式方法

## 相关文档

- [Agent Mode Usage Guide](../agent-mode.md)
- [LangChain Migration Guide](./langchain-migration.md)

---

**最后更新**: 2024-12-28  
**版本**: 1.0.0  
**状态**: ✅ 已修复

