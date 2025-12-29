# Change: 增强 Agent 模式思考过程展示和流式输出

## Why
当前 Agent 模式在执行 ReAct 循环时，用户无法完全看到 Agent 的决策过程。具体来说：
1. Agent 选择哪个工具的思考过程没有明确展示
2. Agent 判断是否还需要调用其他工具的思考过程没有展示
3. 在双 LLM 模式下，最后一步使用 answer_llm 生成答案时使用的是非流式输出，用户体验不够流畅

这些改进将提升用户对 Agent 决策过程的理解，并改善交互体验。

## What Changes
- 在 UI 中明确展示 Agent 选择工具的思考过程（reasoning before action）
- 在 UI 中明确展示 Agent 判断是否继续调用工具的思考过程（reasoning after observation）
- 确保 Agent 模式中最后一步使用 answer_llm 生成答案时采用流式输出
- 优化思考过程的展示格式，使其更清晰易读

## Impact
- Affected specs: agent-mode
- Affected code:
  - `src/agents/react_agent.py` - 增强 stream 方法，确保所有思考过程都被捕获和展示
  - `src/agents/react_agent.py` - 确保 answer_llm 使用流式输出
  - `app.py` - 优化 UI 展示逻辑，更好地展示思考过程

