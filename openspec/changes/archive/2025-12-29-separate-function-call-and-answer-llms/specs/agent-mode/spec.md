# agent-mode 规范变更 - 双 LLM 支持

## MODIFIED Requirements

### Requirement: Agent 模式
系统必须（SHALL）提供 Agent 模式,允许 LLM 自主决策是否需要搜索以及搜索什么内容,实现完整的 ReAct (Reasoning + Acting) 循环。系统必须（SHALL）支持为 Agent 配置两个独立的 LLM 模型：一个用于工具调用决策，另一个用于生成最终回答。

#### Scenario: 启用 Agent 模式
- **WHEN** 用户在模式选择器中选择 "Agent 模式"
- **THEN** 系统切换到 Agent 模式
- **AND** 后续对话使用 Agent 处理流程
- **AND** 系统发送确认消息说明 Agent 模式已启用

#### Scenario: Agent 自主决策搜索
- **WHEN** 用户在 Agent 模式下提问
- **THEN** Agent 使用 function_call_llm 分析问题并决定是否需要搜索
- **AND** 如果需要搜索,Agent 自主生成搜索查询
- **AND** 如果不需要搜索,Agent 直接基于已有知识回答

#### Scenario: Agent 多轮搜索
- **WHEN** Agent 发现第一次搜索结果不足以回答问题
- **THEN** Agent 使用 function_call_llm 决定执行额外的搜索
- **AND** Agent 生成新的搜索查询
- **AND** Agent 综合所有搜索结果后,使用 answer_llm 生成最终回答

#### Scenario: Agent 执行过程可视化
- **WHEN** Agent 执行 ReAct 循环
- **THEN** 系统在 UI 中实时展示每个步骤
- **AND** 展示 Agent 的思考过程（使用 function_call_llm）
- **AND** 展示工具调用 (搜索查询)
- **AND** 展示工具执行结果 (搜索结果)
- **AND** 展示最终回答（使用 answer_llm）
- **AND** 明确标识当前使用的模型（工具调用阶段 vs 回答生成阶段）

#### Scenario: 双模型配置
- **WHEN** 用户配置 Agent 使用两个不同的模型
- **THEN** 系统使用 function_call_llm 进行工具调用决策
- **AND** 系统使用 answer_llm 生成最终回答
- **AND** 两个模型可以来自不同的提供商或使用不同的参数

#### Scenario: 单模型兼容模式
- **WHEN** 用户只配置一个模型或未指定 answer_llm
- **THEN** 系统使用同一模型进行工具调用和回答生成
- **AND** 行为与之前的单模型模式完全一致
- **AND** 保持向后兼容性

## ADDED Requirements

### Requirement: 双 LLM 模型配置
系统必须（SHALL）支持为 Agent 配置两个独立的 LLM 模型实例，分别用于工具调用决策和最终回答生成。

#### Scenario: 环境变量配置
- **WHEN** 用户通过环境变量配置双模型
- **THEN** 系统读取 `AGENT_FUNCTION_CALL_MODEL` 配置工具调用模型
- **AND** 系统读取 `AGENT_ANSWER_MODEL` 配置回答生成模型
- **AND** 配置格式为 JSON 字符串，包含模型提供商和参数

#### Scenario: 代码配置
- **WHEN** 用户在代码中创建 Agent 实例
- **THEN** 可以通过 `function_call_llm` 参数指定工具调用模型
- **AND** 可以通过 `answer_llm` 参数指定回答生成模型
- **AND** 如果未指定 `answer_llm`，则使用 `function_call_llm` 作为回答模型

#### Scenario: UI 配置
- **WHEN** 用户通过 Chainlit UI 配置 Agent
- **THEN** 系统提供独立的模型选择器用于工具调用模型
- **AND** 系统提供独立的模型选择器用于回答生成模型
- **AND** 用户可以分别为两个阶段选择不同的模型和参数

#### Scenario: 配置验证
- **WHEN** 用户配置 Agent 模型
- **THEN** 系统验证至少 function_call_llm 已配置
- **AND** 如果 answer_llm 未配置，系统自动使用 function_call_llm
- **AND** 如果配置无效，系统返回清晰的错误信息

### Requirement: 工具调用结果评估
系统必须（SHALL）实现工具调用结果评估机制，判断工具调用结果是否足够回答用户问题，并决定何时停止工具调用循环并切换到回答生成阶段。

#### Scenario: 基于调用次数的评估
- **WHEN** Agent 执行工具调用循环
- **THEN** 系统跟踪工具调用次数
- **AND** 当调用次数达到配置的最大值（默认 5 次）时，停止循环
- **AND** 切换到回答生成阶段

#### Scenario: 基于结果质量的评估
- **WHEN** 工具返回执行结果
- **THEN** 系统评估结果是否为空或长度不足
- **AND** 如果结果为空或长度不足，继续工具调用循环
- **AND** 如果结果足够，可以提前停止循环并切换到回答生成

#### Scenario: 可配置的评估策略
- **WHEN** 用户配置 Agent 评估参数
- **THEN** 系统支持配置最大工具调用次数
- **AND** 系统支持配置结果质量阈值
- **AND** 系统支持自定义评估函数（可选）

#### Scenario: 评估结果展示
- **WHEN** Agent 完成工具调用结果评估
- **THEN** 系统在 UI 中展示评估结果
- **AND** 说明为何停止工具调用循环
- **AND** 展示将切换到回答生成阶段的提示

### Requirement: 分阶段模型使用
系统必须（SHALL）在 Agent 执行的不同阶段使用相应的 LLM 模型，确保工具调用阶段使用 function_call_llm，回答生成阶段使用 answer_llm。

#### Scenario: 工具调用阶段使用 function_call_llm
- **WHEN** Agent 开始处理用户问题
- **THEN** 系统使用 function_call_llm 进行推理和工具调用决策
- **AND** 所有工具调用相关的 LLM 调用都使用 function_call_llm
- **AND** 在 UI 中标识当前使用的是工具调用模型

#### Scenario: 回答生成阶段使用 answer_llm
- **WHEN** Agent 完成工具调用循环并准备生成最终回答
- **THEN** 系统切换到 answer_llm
- **AND** 使用 answer_llm 基于工具调用结果生成最终回答
- **AND** 在 UI 中标识当前使用的是回答生成模型

#### Scenario: 模型切换提示
- **WHEN** Agent 从工具调用阶段切换到回答生成阶段
- **THEN** 系统在 UI 中显示模型切换提示
- **AND** 说明切换的原因（工具调用结果已满足要求）
- **AND** 展示使用的模型信息

#### Scenario: 流式输出支持
- **WHEN** Agent 使用双模型执行任务
- **THEN** 工具调用阶段的流式输出使用 function_call_llm
- **AND** 回答生成阶段的流式输出使用 answer_llm
- **AND** 两个阶段的流式输出无缝衔接

### Requirement: 成本和使用统计
系统必须（SHALL）分别统计两个模型的使用情况，包括 token 消耗、调用次数和耗时，帮助用户了解成本分布。

#### Scenario: 分别统计 token 使用
- **WHEN** Agent 完成执行
- **THEN** 系统分别统计 function_call_llm 和 answer_llm 的 token 使用
- **AND** 在 UI 中展示两个模型的 token 消耗
- **AND** 展示总 token 消耗和成本估算

#### Scenario: 分别统计调用次数
- **WHEN** Agent 完成执行
- **THEN** 系统统计 function_call_llm 的调用次数（工具调用决策）
- **AND** 系统统计 answer_llm 的调用次数（回答生成）
- **AND** 在 UI 中展示两个模型的调用统计

#### Scenario: 分别统计执行时间
- **WHEN** Agent 完成执行
- **THEN** 系统分别统计工具调用阶段和回答生成阶段的耗时
- **AND** 在 UI 中展示各阶段的耗时分布
- **AND** 帮助用户优化模型选择

