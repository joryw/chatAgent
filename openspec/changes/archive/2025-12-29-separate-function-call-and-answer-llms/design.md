# 双 LLM Agent 架构设计文档

## Context

### 背景
当前 ReAct Agent 使用单一 LLM 模型同时处理工具调用决策和最终回答生成。这种设计虽然简单，但限制了成本优化和性能调优的灵活性。

### 约束条件
- 必须保持现有 Agent 模式的向后兼容性
- 必须使用 LangChain/LangGraph 框架（已是项目依赖）
- 必须支持流式输出和实时展示
- 需要控制 token 消耗和响应延迟
- 必须支持多模型提供商（OpenAI, Anthropic, DeepSeek）

### 利益相关方
- **最终用户**: 需要更灵活的成本和性能控制
- **开发者**: 需要清晰的架构和易于维护的代码
- **系统**: 需要控制成本和性能

## Goals / Non-Goals

### Goals
1. ✅ 支持为 Agent 配置两个独立的 LLM 模型
2. ✅ 工具调用阶段使用 function_call_llm
3. ✅ 回答生成阶段使用 answer_llm
4. ✅ 实现工具调用结果评估机制
5. ✅ 保持向后兼容（单模型模式）
6. ✅ 支持流式输出和实时展示

### Non-Goals
- ❌ 不支持动态模型切换（运行时切换）
- ❌ 不支持多模型并行调用（未来功能）
- ❌ 不支持模型链式调用（未来功能）
- ❌ 不实现复杂的模型路由策略（未来功能）

## Decisions

### Decision 1: 双模型架构设计

**选择**: 在 Agent 初始化时配置两个独立的 LLM 实例

**理由**:
- 清晰的职责分离：工具调用和回答生成使用不同模型
- 灵活性：用户可以根据需求选择不同模型
- 成本优化：可以使用经济的模型做决策，高质量模型生成回答
- 性能优化：可以使用快速模型做决策，减少延迟

**替代方案**:
- **运行时模型切换**: 增加复杂度，需要动态管理模型实例
- **模型路由策略**: 过度设计，当前需求不需要

**决策**: 采用双模型架构，在初始化时配置两个模型实例

### Decision 2: 工具调用结果评估策略

**选择**: 基于工具调用次数和结果质量的简单评估策略

**理由**:
- 简单有效：不需要复杂的评估模型
- 可配置：允许用户调整评估阈值
- 性能友好：不增加额外的 LLM 调用

**评估标准**:
1. 工具调用次数达到上限（默认 5 次）
2. 工具返回结果不为空且长度足够
3. 用户可配置的评估函数（可选）

**替代方案**:
- **使用 LLM 评估**: 增加成本和延迟
- **基于置信度评估**: 需要额外的模型输出

**决策**: 采用基于规则和配置的评估策略

### Decision 3: 向后兼容策略

**选择**: 如果只提供一个模型，两个阶段使用同一模型

**理由**:
- 最小化破坏性变更
- 现有代码无需修改即可工作
- 渐进式迁移路径

**实现方式**:
```python
if answer_llm is None:
    answer_llm = function_call_llm
```

**决策**: 采用向后兼容策略，确保现有代码继续工作

### Decision 4: 配置接口设计

**选择**: 支持环境变量和代码配置两种方式

**环境变量**:
- `AGENT_FUNCTION_CALL_MODEL`: 工具调用模型配置（JSON 格式）
- `AGENT_ANSWER_MODEL`: 回答生成模型配置（JSON 格式）

**代码配置**:
```python
agent = ReActAgent(
    function_call_llm=llm1,
    answer_llm=llm2,
    search_tool=search_tool
)
```

**决策**: 支持两种配置方式，提供灵活性

## Architecture

### 执行流程

```
用户输入
    ↓
[工具调用阶段 - function_call_llm]
    ↓
工具调用决策 → 执行工具 → 观察结果
    ↓
评估结果是否足够？
    ├─ 否 → 继续工具调用循环
    └─ 是 → 进入回答生成阶段
    ↓
[回答生成阶段 - answer_llm]
    ↓
生成最终回答
    ↓
返回结果
```

### 组件设计

```
ReActAgent
├── function_call_llm: BaseChatModel
├── answer_llm: BaseChatModel
├── tools: List[BaseTool]
├── config: AgentConfig
└── agent_executor: AgentExecutor (使用 function_call_llm)
```

### 关键方法

```python
async def run(self, user_input: str) -> AgentResult:
    # 1. 使用 function_call_llm 进行工具调用循环
    tool_results = await self._execute_tool_calling_loop(user_input)
    
    # 2. 评估工具调用结果
    if self._should_generate_answer(tool_results):
        # 3. 使用 answer_llm 生成最终回答
        final_answer = await self._generate_answer(user_input, tool_results)
        return AgentResult(final_answer=final_answer, ...)
```

## Risks / Trade-offs

### 风险
1. **复杂度增加**: 需要管理两个模型实例，增加系统复杂度
   - **缓解**: 清晰的接口设计和文档
2. **配置错误**: 用户可能配置错误的模型组合
   - **缓解**: 配置验证和错误提示
3. **性能影响**: 模型切换可能增加延迟
   - **缓解**: 异步处理和流式输出

### 权衡
- **灵活性 vs 复杂度**: 增加灵活性但增加复杂度
- **成本 vs 质量**: 可以使用经济模型降低成本，但需要确保质量
- **性能 vs 功能**: 双模型可能增加延迟，但提供更好的控制

## Migration Plan

### 阶段 1: 实现双模型支持
1. 修改 `AgentConfig` 支持双模型配置
2. 重构 `ReActAgent` 支持双模型
3. 实现工具调用结果评估
4. 实现回答生成阶段

### 阶段 2: UI 集成
1. 更新 Chainlit UI 支持双模型配置
2. 添加模型选择界面
3. 更新执行过程展示

### 阶段 3: 测试和文档
1. 编写测试用例
2. 更新文档
3. 添加配置示例

### 回滚计划
- 如果出现问题，可以回退到单模型模式
- 保持向后兼容，现有代码继续工作

## Open Questions

1. **评估策略**: 是否需要更复杂的评估机制？
   - 当前：基于规则和配置
   - 未来：可以考虑使用 LLM 评估（如果需求明确）

2. **模型选择建议**: 是否需要提供模型选择建议？
   - 当前：用户自行选择
   - 未来：可以提供推荐配置

3. **性能监控**: 是否需要监控两个模型的性能？
   - 当前：基本日志
   - 未来：详细的性能指标

