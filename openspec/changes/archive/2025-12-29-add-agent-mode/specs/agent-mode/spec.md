# agent-mode 规范变更

## ADDED Requirements

### Requirement: Agent 模式
系统必须（SHALL）提供 Agent 模式,允许 LLM 自主决策是否需要搜索以及搜索什么内容,实现完整的 ReAct (Reasoning + Acting) 循环。

#### Scenario: 启用 Agent 模式
- **WHEN** 用户在模式选择器中选择 "Agent 模式"
- **THEN** 系统切换到 Agent 模式
- **AND** 后续对话使用 Agent 处理流程
- **AND** 系统发送确认消息说明 Agent 模式已启用

#### Scenario: Agent 自主决策搜索
- **WHEN** 用户在 Agent 模式下提问
- **THEN** Agent 分析问题并决定是否需要搜索
- **AND** 如果需要搜索,Agent 自主生成搜索查询
- **AND** 如果不需要搜索,Agent 直接基于已有知识回答

#### Scenario: Agent 多轮搜索
- **WHEN** Agent 发现第一次搜索结果不足以回答问题
- **THEN** Agent 决定执行额外的搜索
- **AND** Agent 生成新的搜索查询
- **AND** Agent 综合所有搜索结果生成最终回答

#### Scenario: Agent 执行过程可视化
- **WHEN** Agent 执行 ReAct 循环
- **THEN** 系统在 UI 中实时展示每个步骤
- **AND** 展示 Agent 的思考过程
- **AND** 展示工具调用 (搜索查询)
- **AND** 展示工具执行结果 (搜索结果)
- **AND** 展示最终回答

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
系统必须（SHALL）将搜索功能封装为 LangChain Tool,供 Agent 使用。

#### Scenario: 工具定义
- **WHEN** 系统初始化 Agent
- **THEN** 创建 SearchTool 实例
- **AND** 定义工具名称为 "web_search"
- **AND** 定义工具描述说明其用途和使用场景
- **AND** 定义工具输入 schema (query: str)

#### Scenario: 工具调用
- **WHEN** Agent 决定使用搜索工具
- **THEN** Agent 生成搜索查询作为工具输入
- **AND** 工具执行搜索并返回格式化结果
- **AND** 结果包含标题、URL、摘要和编号

#### Scenario: 工具错误处理
- **WHEN** 搜索工具执行失败
- **THEN** 工具返回错误信息而非抛出异常
- **AND** Agent 接收错误信息并决定下一步行动
- **AND** 在 UI 中展示工具执行失败的提示

#### Scenario: 工具结果格式化
- **WHEN** 搜索工具返回结果
- **THEN** 结果格式化为易于 Agent 理解的文本
- **AND** 包含每个结果的编号、标题和摘要
- **AND** 限制每个结果的长度 (最多 200 字符)

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

