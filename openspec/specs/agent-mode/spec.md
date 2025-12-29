# agent-mode Specification

## Purpose
TBD - created by archiving change add-agent-mode. Update Purpose after archive.
## Requirements
### Requirement: Agent 模式
系统必须（SHALL）提供 Agent 模式,允许 LLM 自主决策是否需要搜索以及搜索什么内容,实现完整的 ReAct (Reasoning + Acting) 循环。系统必须（SHALL）支持为 Agent 配置两个独立的 LLM 模型：一个用于工具调用决策，另一个用于生成最终回答。系统必须（SHALL）支持使用本地工具（如搜索工具）和 MCP 工具（如高德地图工具）。

#### Scenario: 启用 Agent 模式
- **WHEN** 用户在模式选择器中选择 "Agent 模式"
- **THEN** 系统切换到 Agent 模式
- **AND** 后续对话使用 Agent 处理流程
- **AND** 系统发送确认消息说明 Agent 模式已启用
- **AND** Agent 可以使用所有注册的工具（包括本地工具和 MCP 工具）

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
- **AND** 展示工具调用 (搜索查询、MCP 工具调用等)
- **AND** 展示工具执行结果 (搜索结果、MCP 工具结果等)
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

#### Scenario: Agent 使用 MCP 工具
- **WHEN** Agent 需要调用 MCP 工具（如高德地图路径规划）
- **THEN** Agent 识别可用的 MCP 工具
- **AND** Agent 生成正确的工具调用参数
- **AND** 系统通过 MCP Client 调用工具
- **AND** 工具结果返回给 Agent 用于生成回答

#### Scenario: Agent 混合使用多种工具
- **WHEN** Agent 需要同时使用本地工具和 MCP 工具
- **THEN** Agent 可以自主选择使用哪个工具
- **AND** Agent 可以在一次对话中调用多个不同类型的工具
- **AND** Agent 综合所有工具的结果生成最终回答

### Requirement: ReAct 循环
系统必须（SHALL）实现 ReAct (Reasoning + Acting) 循环,包括思考、行动、观察、再思考的完整流程。

#### Scenario: Reasoning 阶段
- **WHEN** Agent 开始处理用户问题或观察到新信息
- **THEN** Agent 进行推理思考
- **AND** 决定下一步行动 (搜索、回答或再次思考)
- **AND** 在 UI 中展示思考内容

#### Scenario: Acting 阶段
- **WHEN** Agent 决定需要执行搜索
- **THEN** Agent 生成具体的搜索查询
- **AND** 调用搜索工具执行搜索
- **AND** 在 UI 中展示工具调用信息

#### Scenario: Observing 阶段
- **WHEN** 搜索工具返回结果
- **THEN** Agent 观察和分析搜索结果
- **AND** 在 UI 中展示搜索结果摘要
- **AND** 决定是否需要更多信息

#### Scenario: 循环终止
- **WHEN** Agent 判断已有足够信息回答问题
- **THEN** Agent 停止循环
- **AND** 生成最终回答
- **AND** 在 UI 中展示完整回答

#### Scenario: 最大迭代限制
- **WHEN** Agent 执行迭代次数达到上限 (默认 5 次)
- **THEN** 系统强制停止循环
- **AND** Agent 基于已有信息生成回答
- **AND** 在 UI 中提示已达到迭代上限

### Requirement: 搜索工具封装
系统必须（SHALL）将搜索功能封装为 LangChain Tool,供 Agent 使用。系统必须（SHALL）支持将 MCP 工具也封装为 LangChain Tool，与搜索工具一起供 Agent 使用。

#### Scenario: 工具定义
- **WHEN** 系统初始化 Agent
- **THEN** 创建 SearchTool 实例
- **AND** 创建 MCP Tool 实例（如果 MCP 服务器可用）
- **AND** 定义工具名称为 "web_search" 和 MCP 工具名称
- **AND** 定义工具描述说明其用途和使用场景
- **AND** 定义工具输入 schema

#### Scenario: 工具调用
- **WHEN** Agent 决定使用搜索工具或 MCP 工具
- **THEN** Agent 生成工具查询作为工具输入
- **AND** 工具执行并返回格式化结果
- **AND** 结果包含标题、URL、摘要和编号（搜索工具）或结构化数据（MCP 工具）

#### Scenario: 工具错误处理
- **WHEN** 搜索工具或 MCP 工具执行失败
- **THEN** 工具返回错误信息而非抛出异常
- **AND** Agent 接收错误信息并决定下一步行动
- **AND** Agent 可以选择使用其他工具或基于已有信息回答

### Requirement: Agent 配置
系统必须（SHALL）支持配置 Agent 的行为参数。

#### Scenario: 最大迭代次数配置
- **WHEN** 系统初始化 Agent 配置
- **THEN** 从环境变量读取最大迭代次数
- **AND** 默认值为 5 次
- **AND** 允许范围为 1-10 次

#### Scenario: 最大执行时间配置
- **WHEN** 系统初始化 Agent 配置
- **THEN** 从环境变量读取最大执行时间
- **AND** 默认值为 60 秒
- **AND** 允许范围为 10-300 秒

#### Scenario: 执行超时处理
- **WHEN** Agent 执行时间超过配置的最大值
- **THEN** 系统强制停止 Agent 执行
- **AND** 返回已有的中间结果
- **AND** 在 UI 中提示执行超时

#### Scenario: 详细日志配置
- **WHEN** 启用详细日志 (AGENT_VERBOSE=true)
- **THEN** 系统记录 Agent 的每个思考和行动
- **AND** 记录工具调用的输入输出
- **AND** 便于调试和优化

### Requirement: Agent 执行过程展示
系统必须（SHALL）在 UI 中实时展示 Agent 的执行过程,让用户了解 Agent 的决策和行动。

#### Scenario: 思考过程展示
- **WHEN** Agent 进行推理思考
- **THEN** 在 UI 中创建 "思考中..." Step
- **AND** 实时流式更新思考内容
- **AND** 思考完成后自动折叠 Step

#### Scenario: 工具选择思考过程展示
- **WHEN** Agent 决定调用工具之前
- **THEN** 在 UI 中展示 Agent 选择哪个工具的思考过程
- **AND** 展示 Agent 分析为什么选择特定工具的原因
- **AND** 展示 Agent 对工具输入参数的思考
- **AND** 思考过程以流式方式实时更新
- **AND** 思考完成后展示对应的工具调用操作

#### Scenario: 工具调用展示
- **WHEN** Agent 调用搜索工具
- **THEN** 在 UI 中创建 "搜索" Step
- **AND** 展示搜索查询内容
- **AND** 展示搜索状态 (进行中/完成/失败)
- **AND** 工具调用完成后自动折叠 Step

#### Scenario: 搜索结果展示
- **WHEN** 搜索工具返回结果
- **THEN** 在 UI 中创建 "搜索结果" Step
- **AND** 展示找到的结果数量
- **AND** 展示前 3 条结果的标题和摘要
- **AND** 自动折叠 Step

#### Scenario: 继续调用工具判断思考过程展示
- **WHEN** Agent 收到工具执行结果后
- **THEN** 在 UI 中展示 Agent 判断是否还需要调用其他工具的思考过程
- **AND** 展示 Agent 分析工具结果是否足够回答问题的推理
- **AND** 展示 Agent 决定继续调用工具或生成最终答案的决策过程
- **AND** 思考过程以流式方式实时更新
- **AND** 如果决定继续调用工具，展示对应的工具调用操作
- **AND** 如果决定生成最终答案，展示切换到答案生成阶段的提示

#### Scenario: 最终回答展示
- **WHEN** Agent 生成最终回答
- **THEN** 在 UI 中创建独立的消息框
- **AND** 流式展示回答内容
- **AND** 保持 Step 展开状态供用户查看

#### Scenario: 执行步骤折叠
- **WHEN** 用户点击已折叠的执行步骤
- **THEN** 展开并显示完整内容
- **AND** 用户可以查看详细的执行信息

### Requirement: Agent Prompt 模板
系统必须（SHALL）提供精心设计的 Prompt 模板,指导 Agent 的行为。

#### Scenario: 系统提示词定义
- **WHEN** 系统初始化 Agent
- **THEN** 使用 ReAct Prompt 模板
- **AND** 明确说明 Agent 的目标和职责
- **AND** 说明可用的工具和使用方法
- **AND** 提供思考和行动的格式要求

#### Scenario: 工具使用指导
- **WHEN** Prompt 模板定义工具使用规则
- **THEN** 说明何时应该使用搜索工具
- **AND** 说明如何生成有效的搜索查询
- **AND** 说明如何解读搜索结果

#### Scenario: 停止条件说明
- **WHEN** Prompt 模板定义停止规则
- **THEN** 明确说明何时应该停止循环
- **AND** 说明如何生成最终回答
- **AND** 要求回答准确、完整、有引用

#### Scenario: Prompt 优化
- **WHEN** Agent 行为不符合预期
- **THEN** 可以调整 Prompt 模板
- **AND** 通过配置文件管理 Prompt
- **AND** 支持针对不同 LLM 的 Prompt 变体

### Requirement: Agent 错误处理
系统必须（SHALL）实现健壮的错误处理,确保 Agent 模式的稳定性。

#### Scenario: 工具调用失败
- **WHEN** 搜索工具执行失败
- **THEN** 将错误信息返回给 Agent
- **AND** Agent 决定是否重试或使用已有知识
- **AND** 在 UI 中展示工具失败提示

#### Scenario: LLM API 错误
- **WHEN** LLM API 调用失败
- **THEN** 使用现有的重试机制
- **AND** 如果重试失败,停止 Agent 执行
- **AND** 在 UI 中展示友好的错误消息

#### Scenario: 无限循环检测
- **WHEN** Agent 重复执行相同的操作
- **THEN** 系统检测到循环模式
- **AND** 强制停止执行
- **AND** 提示用户重新提问或切换模式

#### Scenario: 异常恢复
- **WHEN** Agent 执行过程中发生异常
- **THEN** 系统捕获异常并记录日志
- **AND** 尝试返回已有的中间结果
- **AND** 如果无法恢复,显示错误消息并建议切换到 Chat 模式

### Requirement: Agent 性能优化
系统必须（SHALL）优化 Agent 的执行性能,控制延迟和成本。

#### Scenario: 流式输出优化
- **WHEN** Agent 生成思考内容或回答
- **THEN** 使用流式输出实时展示
- **AND** 减少用户等待时间感知
- **AND** 提升交互体验

#### Scenario: 并发执行
- **WHEN** 可以并发执行的操作
- **THEN** 使用异步并发提升性能
- **AND** 例如同时展示多个 Step

#### Scenario: Token 使用监控
- **WHEN** Agent 执行完成
- **THEN** 计算并展示总 token 消耗
- **AND** 包括思考、工具调用和回答的 token
- **AND** 帮助用户了解成本

#### Scenario: 搜索结果缓存
- **WHEN** Agent 执行相同的搜索查询
- **THEN** 使用缓存的结果而非重新搜索
- **AND** 减少搜索延迟和负载
- **AND** 缓存有效期为当前会话

### Requirement: LangChain Agent 集成
系统必须（SHALL）正确集成 LangChain Agent 框架,遵循其最佳实践。

#### Scenario: Agent 初始化
- **WHEN** 系统创建 Agent 实例
- **THEN** 使用 LangChain 的 create_react_agent 或自定义实现
- **AND** 配置 LLM、工具列表和 Prompt 模板
- **AND** 设置 Agent 执行器参数 (max_iterations 等)

#### Scenario: Agent 回调
- **WHEN** Agent 执行过程中
- **THEN** 使用 LangChain Callback 捕获事件
- **AND** 监听思考、工具调用、结果等事件
- **AND** 将事件转换为 UI 更新

#### Scenario: Agent 停止
- **WHEN** Agent 完成任务或需要停止
- **THEN** 正确清理 Agent 资源
- **AND** 关闭所有打开的 Step
- **AND** 释放相关内存

#### Scenario: Agent 内存管理
- **WHEN** Agent 执行多轮对话
- **THEN** 维护对话历史和工具调用记录
- **AND** 避免重复执行相同的搜索
- **AND** 在会话结束时清理内存

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
- **AND** 使用流式输出（astream）而非非流式输出（ainvoke）生成最终回答
- **AND** 最终回答以流式方式实时展示在 UI 中

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
- **AND** 回答生成阶段必须使用流式输出，不允许使用非流式输出

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

