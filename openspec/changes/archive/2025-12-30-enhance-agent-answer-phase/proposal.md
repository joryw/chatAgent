# Change: 增强 Agent 回答阶段的推理能力和引用交互

## Why
当前 Agent 模式在双 LLM 配置下存在两个用户体验问题：
1. answer_llm 使用 `ainvoke` 生成最终回答，无法展示模型的推理过程（reasoning），特别是对于 DeepSeek-R1 等推理模型，用户无法看到其思考过程
2. 回答中的引用标记（如 [1][15]）只是纯文本，用户需要滚动到页面底部的引用列表才能查看来源，交互体验不佳

这两个问题影响了用户对 Agent 决策过程的理解和对引用来源的快速访问。

## What Changes
- 修改 `_generate_answer_with_answer_llm` 方法，使用流式输出（`astream`）替代非流式输出（`ainvoke`）
- 在流式输出中提取并展示 answer_llm 的推理内容（reasoning_content）
- 实现引用标记的实时转换，将文本引用 `[数字]` 转换为可点击的 Markdown 链接 `[数字](URL)`
- 在流式输出过程中实时处理引用转换，提供更好的用户交互体验

## Impact
- **Affected specs**: agent-mode
- **Affected code**: 
  - `src/agents/react_agent.py` - 修改 `_generate_answer_with_answer_llm` 方法
  - `src/agents/react_agent.py` - 修改 `run_async` 方法中的回答生成逻辑
  - `src/search/citation_processor.py` - 可能需要扩展引用处理功能

