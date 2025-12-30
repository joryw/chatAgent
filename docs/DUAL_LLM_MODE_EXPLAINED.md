# Agent 模式：单 LLM vs 双 LLM 详解

## 📚 概念解释

### 🤖 单 LLM 模式（Single LLM Mode）

**定义**：使用同一个 LLM 完成所有任务
- 既负责**工具调用决策**（思考、选择工具）
- 又负责**最终答案生成**（基于工具结果回答用户）

**工作流程**：
```
用户问题 → LLM → 思考 → 调用工具 → 观察结果 → LLM → 生成答案
          ↑_____________同一个 LLM_______________↑
```

### 🔄 双 LLM 模式（Dual LLM Mode）

**定义**：使用两个不同的 LLM 分别完成不同任务
- **Function Call LLM**：负责工具调用决策（思考、选择工具）
- **Answer LLM**：负责最终答案生成（基于工具结果回答用户）

**工作流程**：
```
用户问题 → Function Call LLM → 思考 → 调用工具 → 观察结果
                                                          ↓
                                    Answer LLM ← 生成答案
```

---

## 🔧 触发条件

### ✅ 触发双 LLM 模式的条件

**必要条件**：在环境变量中设置 `AGENT_ANSWER_MODEL`

```bash
# .env 文件示例
# 工具调用模型（负责思考和选择工具）
AGENT_FUNCTION_CALL_MODEL='{"provider": "deepseek", "model_name": "deepseek-chat", "temperature": 0.3}'

# 答案生成模型（负责生成最终答案）- 关键！
AGENT_ANSWER_MODEL='{"provider": "openai", "model_name": "gpt-4o", "temperature": 0.7}'
```

**判断逻辑**（代码位置：`src/agents/react_agent.py:257-258`）：
```python
self.function_call_llm = llm
self.answer_llm = answer_llm if answer_llm is not None else llm

# 运行时判断
using_dual_llm = self.answer_llm is not self.function_call_llm
```

**检测点**（代码位置：`src/agents/react_agent.py:453, 617`）：
```python
# 在 run() 和 stream() 方法中
using_dual_llm = self.answer_llm is not self.function_call_llm

if using_dual_llm:
    # 使用双 LLM 模式流程
    logger.info("🔄 切换到 answer_llm 生成最终回答...")
else:
    # 使用单 LLM 模式流程
    logger.info("✅ 使用 function_call_llm 生成最终回答")
```

### ❌ 触发单 LLM 模式的条件

**情况 1：未设置 `AGENT_ANSWER_MODEL`**
```bash
# .env 文件
# 只设置一个模型
AGENT_FUNCTION_CALL_MODEL='{"provider": "deepseek", "model_name": "deepseek-chat"}'
# AGENT_ANSWER_MODEL 未设置或为空
```

**情况 2：两个环境变量都未设置**
```bash
# .env 文件
# 两个都不设置，使用默认模型
# AGENT_FUNCTION_CALL_MODEL 未设置
# AGENT_ANSWER_MODEL 未设置
```
在这种情况下，Agent 会使用当前界面选择的默认模型（如 OpenAI GPT-4o）。

---

## 🎯 使用场景对比

### 🚀 推荐使用双 LLM 模式的场景

1. **专业分工，各司其职**
   ```
   Function Call LLM: DeepSeek-Chat（擅长推理和工具选择）
   Answer LLM: GPT-4o（擅长生成流畅的回答）
   ```

2. **成本优化**
   ```
   Function Call LLM: 便宜的模型（如 DeepSeek）- 处理工具调用
   Answer LLM: 昂贵但高质量的模型（如 GPT-4o）- 只在最后生成答案
   ```

3. **性能优化**
   ```
   Function Call LLM: 快速响应的模型 - 快速决策
   Answer LLM: 慢但质量高的模型 - 生成高质量答案
   ```

4. **特定能力组合**
   ```
   Function Call LLM: DeepSeek Reasoner（深度思考）- 复杂推理
   Answer LLM: GPT-4o（流畅表达）- 用户友好的回答
   ```

### ⚡ 使用单 LLM 模式的场景

1. **简化配置**
   - 不需要配置两个模型
   - 适合快速开始和测试

2. **模型本身很强大**
   - 使用 GPT-4o 或 Claude 3.5 Sonnet
   - 既能做好推理，又能生成好答案

3. **降低延迟**
   - 只需要加载一个模型
   - 减少模型切换开销

---

## 🔍 代码实现细节

### 配置加载（`src/config/agent_config.py:155-212`）

```python
def create_agent_llms_from_config(
    default_provider: str,
    agent_config: Optional[AgentConfig] = None
) -> Tuple[BaseChatModel, Optional[BaseChatModel]]:
    """Create LLM instances for Agent from configuration.
    
    Returns:
        Tuple of (function_call_llm, answer_llm)
        If answer_llm config is not provided, returns None for answer_llm
    """
    # 1. 创建 function_call_llm（必须）
    function_call_llm = ...
    
    # 2. 创建 answer_llm（可选）
    answer_llm = None
    answer_config_json = agent_config.answer_model_config
    if answer_config_json:  # 如果设置了 AGENT_ANSWER_MODEL
        answer_llm = ...  # 创建独立的 answer_llm
    
    return function_call_llm, answer_llm
```

### Agent 初始化（`src/agents/react_agent.py:239-258`）

```python
def __init__(
    self,
    llm: BaseChatModel,  # function_call_llm
    search_tool: SearchTool,
    config: Optional[AgentConfig] = None,
    answer_llm: Optional[BaseChatModel] = None,  # 可选！
    additional_tools: Optional[List[BaseTool]] = None,
):
    self.function_call_llm = llm
    
    # 关键逻辑：如果没有提供 answer_llm，使用 function_call_llm
    self.answer_llm = answer_llm if answer_llm is not None else llm
    
    # 判断是否为双 LLM 模式
    using_dual_llm = answer_llm is not None
```

### 执行流程差异

#### 双 LLM 模式流程（`src/agents/react_agent.py:534-539, 805-891`）

```python
if using_dual_llm:
    # Step 1: Function Call LLM 思考并调用工具
    # (由 LangGraph agent_executor 自动处理)
    tool_results = [...]  # 收集所有工具执行结果
    
    # Step 2: 切换到 Answer LLM 生成最终答案
    logger.info("🔄 切换到 answer_llm 生成最终回答...")
    
    # 构造提示词，包含所有工具结果
    system_prompt = """基于以下搜索结果，为用户提供准确答案..."""
    user_prompt = f"""用户问题: {user_input}
    
搜索结果:
{tool_results}

请回答..."""
    
    # 使用 answer_llm 生成答案
    final_answer = await self.answer_llm.ainvoke(messages)
    
    # 添加引用列表
    citations_list = self.citation_manager.generate_citations_list(...)
    return final_answer + citations_list
```

#### 单 LLM 模式流程（`src/agents/react_agent.py:543-556, 892-957`）

```python
elif not using_dual_llm:
    # Function Call LLM 既思考、调用工具，又生成最终答案
    # (由 LangGraph agent_executor 自动处理)
    
    # 从 agent_executor 的消息中提取最终答案
    final_answer = ...  # 从 AIMessage.content 中提取
    
    # 如果没有找到答案，回退到双 LLM 模式的方法
    if not final_answer:
        logger.warning("⚠️ Agent 未生成最终回答，使用 answer_llm 生成...")
        final_answer = await self._generate_answer_with_answer_llm(...)
    
    # 添加引用处理
    if self.citation_manager and tool_results:
        # 转换引用 [num] → [[num]](url)
        # 生成引用列表
        ...
    
    return final_answer
```

---

## 📊 性能对比

| 维度 | 单 LLM 模式 | 双 LLM 模式 |
|------|------------|-----------|
| **配置复杂度** | ⭐ 简单 | ⭐⭐ 中等 |
| **启动速度** | ⚡⚡⚡ 快 | ⚡⚡ 中等（需加载两个模型） |
| **执行延迟** | ⚡⚡⚡ 低 | ⚡⚡ 稍高（模型切换） |
| **答案质量** | ⭐⭐ 取决于单个模型 | ⭐⭐⭐ 可选择最佳组合 |
| **成本控制** | ⭐⭐ 中等 | ⭐⭐⭐ 灵活（便宜+贵） |
| **灵活性** | ⭐⭐ 有限 | ⭐⭐⭐ 高 |

---

## 💡 实际配置示例

### 示例 1：高性价比配置（推荐）

```bash
# 使用 DeepSeek 处理工具调用（便宜、快速、推理能力强）
AGENT_FUNCTION_CALL_MODEL='{"provider": "deepseek", "model_name": "deepseek-chat", "temperature": 0.3, "max_tokens": 1000}'

# 使用 GPT-4o 生成最终答案（质量高、表达流畅）
AGENT_ANSWER_MODEL='{"provider": "openai", "model_name": "gpt-4o", "temperature": 0.7, "max_tokens": 2000}'
```

**优势**：
- ✅ 工具调用阶段便宜（DeepSeek）
- ✅ 最终答案质量高（GPT-4o）
- ✅ 总体成本降低 50-70%

### 示例 2：全能单模型配置

```bash
# 只使用 GPT-4o
AGENT_FUNCTION_CALL_MODEL='{"provider": "openai", "model_name": "gpt-4o", "temperature": 0.5}'
# AGENT_ANSWER_MODEL 不设置
```

**优势**：
- ✅ 配置简单
- ✅ 质量稳定
- ✅ 延迟最低

### 示例 3：极致推理配置

```bash
# 使用 DeepSeek Reasoner 深度思考
AGENT_FUNCTION_CALL_MODEL='{"provider": "deepseek", "model_name": "deepseek-reasoner", "temperature": 0.2}'

# 使用 Claude 生成优雅答案
AGENT_ANSWER_MODEL='{"provider": "anthropic", "model_name": "claude-3-5-sonnet-20241022", "temperature": 0.7}'
```

**优势**：
- ✅ 最强推理能力（DeepSeek Reasoner）
- ✅ 最佳表达能力（Claude）
- ⚠️ 成本和延迟较高

### 示例 4：默认配置（无环境变量）

```bash
# .env 中不设置任何 Agent 模型配置
# AGENT_FUNCTION_CALL_MODEL 不设置
# AGENT_ANSWER_MODEL 不设置
```

**行为**：
- 使用界面选择的默认模型（如 OpenAI GPT-4o）
- 单 LLM 模式运行

---

## 🐛 故障排查

### 问题 1：如何确认当前使用的是哪种模式？

**查看日志**：
```
# 单 LLM 模式
🚀 Agent initialized (max_iterations=10, max_execution_time=120s, dual_llm_mode=False, tools=...)

# 双 LLM 模式
🚀 Agent initialized (max_iterations=10, max_execution_time=120s, dual_llm_mode=True, tools=...)
```

**或在执行时看到**：
```
# 双 LLM 模式
🔄 切换到 answer_llm 生成最终回答...

# 单 LLM 模式
✅ 使用 function_call_llm 生成最终回答
```

### 问题 2：设置了 `AGENT_ANSWER_MODEL` 但没生效？

**检查清单**：
1. ✅ 环境变量格式正确（JSON 字符串）
2. ✅ 重启了应用（修改 `.env` 需要重启）
3. ✅ 检查日志中的 `dual_llm_mode` 值

**验证方法**：
```bash
# 打印环境变量
echo $AGENT_ANSWER_MODEL

# 或在 Python 中
import os
print(os.getenv("AGENT_ANSWER_MODEL"))
```

### 问题 3：双 LLM 模式报错？

**常见错误**：
```
❌ Failed to initialize answer_llm: Invalid provider
```

**解决方案**：
- 检查 `provider` 是否正确（`openai`, `anthropic`, `deepseek`）
- 检查对应的 API Key 是否配置（`OPENAI_API_KEY` 等）
- 检查 JSON 格式是否正确（使用单引号包裹，内部使用双引号）

---

## 🎓 总结

| 特性 | 单 LLM 模式 | 双 LLM 模式 |
|------|-----------|-----------|
| **触发条件** | 不设置 `AGENT_ANSWER_MODEL` | 设置 `AGENT_ANSWER_MODEL` |
| **适用场景** | 简单快速、单一强模型 | 专业分工、成本优化 |
| **推荐人群** | 新手、快速测试 | 高级用户、生产环境 |
| **最佳实践** | GPT-4o 单模型 | DeepSeek + GPT-4o 组合 |

---

## 📚 相关文档

- [Agent 模式规范](../../openspec/specs/agent-mode/spec.md)
- [双 LLM 实现总结](../../openspec/changes/archive/2025-12-29-separate-function-call-and-answer-llms/IMPLEMENTATION_SUMMARY.md)
- [Agent 配置指南](../../openspec/specs/agent-mode/spec.md#configuration)

---

## 🔗 代码参考

- **配置加载**：`src/config/agent_config.py`
- **Agent 实现**：`src/agents/react_agent.py`
- **应用集成**：`app.py`

