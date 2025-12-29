# 双 LLM Agent 实施总结

## 实施完成情况

### ✅ 已完成的功能

1. **配置支持**
   - ✅ `AgentConfig` 支持双模型配置字段
   - ✅ 环境变量支持 (`AGENT_FUNCTION_CALL_MODEL`, `AGENT_ANSWER_MODEL`)
   - ✅ JSON 配置解析和验证

2. **核心 Agent 实现**
   - ✅ `ReActAgent` 支持双 LLM 参数 (`function_call_llm`, `answer_llm`)
   - ✅ 向后兼容：如果只提供一个 LLM，两个阶段使用同一模型
   - ✅ 工具调用结果评估机制
   - ✅ 使用 `answer_llm` 生成最终回答

3. **流式输出支持**
   - ✅ `stream` 方法支持双模型切换
   - ✅ 工具调用阶段使用 `function_call_llm`
   - ✅ 回答生成阶段使用 `answer_llm` 流式输出

4. **应用集成**
   - ✅ `app.py` 更新支持双模型配置
   - ✅ 辅助函数 `create_agent_llms_from_config` 创建模型实例
   - ✅ 所有 Agent 创建位置已更新

## 使用方法

### 环境变量配置

```bash
# 工具调用模型配置（JSON 格式）
AGENT_FUNCTION_CALL_MODEL='{"provider": "deepseek", "model_name": "deepseek-chat", "temperature": 0.3, "max_tokens": 1000}'

# 回答生成模型配置（JSON 格式，可选）
AGENT_ANSWER_MODEL='{"provider": "openai", "model_name": "gpt-4", "temperature": 0.7, "max_tokens": 2000}'
```

### 代码使用

```python
from src.agents import ReActAgent
from src.config.agent_config import create_agent_llms_from_config, get_agent_config

# 创建双模型实例
agent_config = get_agent_config()
function_call_llm, answer_llm = create_agent_llms_from_config(
    default_provider="openai",
    agent_config=agent_config
)

# 创建 Agent
agent = ReActAgent(
    llm=function_call_llm,
    search_tool=search_tool,
    config=agent_config,
    answer_llm=answer_llm,  # 可选，如果为 None 则使用 function_call_llm
)
```

## 架构说明

### 执行流程

1. **工具调用阶段**（使用 `function_call_llm`）
   - Agent 使用 `function_call_llm` 进行推理和工具调用决策
   - 执行工具调用（如搜索）
   - 收集工具调用结果

2. **结果评估**
   - 检查工具调用次数是否达到上限
   - 评估工具调用结果是否足够

3. **回答生成阶段**（使用 `answer_llm`）
   - 如果使用双模型模式，切换到 `answer_llm`
   - 基于工具调用结果生成最终回答
   - 流式输出回答内容

### 向后兼容

- 如果未配置 `answer_llm`，两个阶段使用同一模型
- 现有代码无需修改即可继续工作
- 单模型模式的行为与之前完全一致

## 配置示例

### 示例 1: 使用经济模型做决策，高质量模型生成回答

```bash
AGENT_FUNCTION_CALL_MODEL='{"provider": "deepseek", "model_name": "deepseek-chat", "temperature": 0.3}'
AGENT_ANSWER_MODEL='{"provider": "openai", "model_name": "gpt-4", "temperature": 0.7}'
```

### 示例 2: 单模型模式（向后兼容）

```bash
# 不设置 AGENT_FUNCTION_CALL_MODEL 和 AGENT_ANSWER_MODEL
# Agent 将使用默认模型进行所有操作
```

## 注意事项

1. **配置格式**: 环境变量必须是有效的 JSON 字符串
2. **Provider 支持**: 支持所有已配置的 provider (openai, anthropic, deepseek)
3. **API Key**: 模型配置中的 provider 必须对应有效的 API key
4. **性能**: 双模型模式会增加一次 LLM 调用，但可以提供更好的成本和质量平衡

## 后续改进建议

1. UI 配置界面：在 Chainlit UI 中添加双模型配置选项
2. 模型选择建议：提供推荐的模型组合配置
3. 性能监控：分别统计两个模型的 token 使用和耗时
4. 评估策略优化：实现更智能的工具调用结果评估

