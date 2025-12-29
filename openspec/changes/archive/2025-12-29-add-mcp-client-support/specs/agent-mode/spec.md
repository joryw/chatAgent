# agent-mode 规范变更

## MODIFIED Requirements

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

