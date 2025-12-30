# Agent 回答阶段增强功能使用说明

## 概述

本次更新为 Agent 模式的回答生成阶段添加了两个重要的用户体验改进：

1. **推理过程展示**: 展示 answer_llm 的推理过程，特别是对于 DeepSeek-R1 等推理模型
2. **可点击的引用链接**: 将引用标记自动转换为可点击的链接

## 功能详情

### 1. 推理过程展示

#### 适用场景
- 使用双 LLM 模式（配置了 `answer_llm`）
- answer_llm 使用支持推理的模型（如 DeepSeek-R1）

#### 工作原理
- 系统检测 answer_llm 流式输出中的 `reasoning_content` 字段
- 在 UI 中创建独立的"思考回答方式..."步骤展示推理内容
- 推理内容与最终回答分开显示，便于用户理解模型的决策过程

#### 配置示例

```bash
# 在 .env 文件中配置双 LLM 模式
AGENT_FUNCTION_CALL_MODEL='{"provider": "deepseek", "model_name": "deepseek-chat"}'
AGENT_ANSWER_MODEL='{"provider": "deepseek", "model_name": "deepseek-reasoner"}'
```

#### UI 展示
```
🧠 思考回答方式...
[展示 DeepSeek-R1 的推理过程]

💬 最终回答
[展示生成的回答内容]
```

### 2. 可点击的引用链接

#### 适用场景
- Agent 模式下进行了搜索
- 回答中包含引用标记（如 [1]、[15]）

#### 工作原理
- 系统自动检测回答中的引用标记 `[数字]`
- 从 GlobalCitationManager 获取对应的 URL
- 转换为 Markdown 链接格式 `[[数字]](URL)`
- Chainlit UI 自动将其渲染为可点击的链接

#### 引用格式

**原始格式**:
```
根据研究[1]，AI技术发展迅速[2]。
```

**转换后格式**:
```
根据研究[[1]](https://example.com/article1)，AI技术发展迅速[[2]](https://example.com/article2)。
```

**UI 展示**:
- 引用编号 [1] 和 [2] 显示为蓝色可点击链接
- 点击后在新标签页打开对应的来源网页
- 无需滚动到页面底部查看引用列表

### 3. 引用列表

在回答末尾，系统会自动添加完整的引用列表：

```markdown
---
📚 引用文章列表:

**第 1 次搜索** (查询: AI 开源项目 2025)
1. [[Article Title 1]](https://example.com/1) - `example.com`
2. [[Article Title 2]](https://example.com/2) - `example.com`

**第 2 次搜索** (查询: AI 项目排名)
3. [[Article Title 3]](https://example.com/3) - `another.com`
```

## 技术实现

### 核心改动

1. **新增方法**: `_generate_answer_with_answer_llm_streaming`
   - 使用 `astream` 替代 `ainvoke` 进行流式输出
   - 检测并提取 `reasoning_content`
   - 通过 `AgentStep` yield 推理和回答内容

2. **引用处理**: 
   - 利用 `CitationProcessor` 进行引用转换
   - 使用 `GlobalCitationManager` 管理多轮搜索的全局引用编号
   - 在流式输出完成后添加引用列表

3. **向后兼容**:
   - 保留非流式的 fallback 方法
   - 单 LLM 模式不受影响
   - 不支持推理的模型正常工作

### 测试

运行测试脚本验证功能：

```bash
# 测试引用转换功能
python test_citation_conversion_simple.py

# 测试完整的 Agent 流程（需要配置真实模型）
python test_agent_answer_phase.py
```

## 常见问题

### Q: 为什么使用双括号格式 [[num]](url)？
A: 双括号格式保持了引用编号的可见性，用户可以看到 [1]、[2] 等编号，同时又能点击跳转。单括号格式 [num](url) 在 Markdown 中只显示编号，不显示括号。

### Q: 如果 answer_llm 不支持推理怎么办？
A: 系统会自动检测，如果没有 `reasoning_content`，则不会创建推理步骤，直接展示回答内容。

### Q: 引用链接在哪里点击？
A: 在回答内容中，所有的 [数字] 格式都会显示为蓝色可点击链接，点击即可跳转到来源网页。

### Q: 单 LLM 模式是否受影响？
A: 不受影响。单 LLM 模式继续使用 function_call_llm 生成回答，引用处理逻辑保持不变。

## 相关文档

- OpenSpec 提案: `openspec/changes/enhance-agent-answer-phase/proposal.md`
- 规范变更: `openspec/changes/enhance-agent-answer-phase/specs/agent-mode/spec.md`
- 实施任务: `openspec/changes/enhance-agent-answer-phase/tasks.md`

