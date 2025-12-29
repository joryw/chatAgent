## MODIFIED Requirements

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

