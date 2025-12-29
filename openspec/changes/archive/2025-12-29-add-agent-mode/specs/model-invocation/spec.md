# model-invocation 规范变更

## ADDED Requirements

### Requirement: 对话模式选择
系统必须（SHALL）提供对话模式选择功能,允许用户在 Chat 模式和 Agent 模式之间切换。

#### Scenario: 模式选择器显示
- **WHEN** 用户会话开始时
- **THEN** 系统在设置面板中显示模式选择器
- **AND** 选择器包含 "Chat 模式" 和 "Agent 模式" 两个选项
- **AND** 显示每种模式的简短说明

#### Scenario: 默认模式配置
- **WHEN** 系统初始化时
- **THEN** 从环境变量读取默认模式 (DEFAULT_MODE)
- **AND** 如果未配置,默认使用 Chat 模式
- **AND** 在欢迎消息中说明当前模式

#### Scenario: 模式切换
- **WHEN** 用户在选择器中切换模式
- **THEN** 系统立即切换到新模式
- **AND** 清除当前对话历史
- **AND** 发送确认消息说明已切换到新模式

#### Scenario: 模式说明
- **WHEN** 用户查看模式选择器
- **THEN** Chat 模式说明: "常规对话,可手动启用联网搜索"
- **AND** Agent 模式说明: "智能助手,自动决策是否需要联网搜索"

### Requirement: Chat 模式处理
系统必须（SHALL）在 Chat 模式下保持现有的对话处理逻辑。

#### Scenario: Chat 模式消息处理
- **WHEN** 用户在 Chat 模式下发送消息
- **THEN** 系统使用现有的消息处理流程
- **AND** 支持手动搜索开关控制
- **AND** 使用流式响应输出

#### Scenario: Chat 模式搜索控制
- **WHEN** 用户在 Chat 模式下
- **THEN** 搜索开关功能正常可用
- **AND** 可以通过 UI 或命令启用/禁用搜索
- **AND** 搜索行为与现有功能完全一致

#### Scenario: Chat 模式向后兼容
- **WHEN** 系统处于 Chat 模式
- **THEN** 所有现有功能正常工作
- **AND** 不受 Agent 模式代码影响
- **AND** 性能和体验不变

### Requirement: Agent 模式处理
系统必须（SHALL）在 Agent 模式下使用 Agent 处理流程。

#### Scenario: Agent 模式消息处理
- **WHEN** 用户在 Agent 模式下发送消息
- **THEN** 系统使用 Agent 处理流程
- **AND** Agent 自主决策是否需要搜索
- **AND** 展示 Agent 执行过程

#### Scenario: Agent 模式搜索开关禁用
- **WHEN** 用户在 Agent 模式下
- **THEN** 搜索开关显示为禁用状态
- **AND** 开关说明: "Agent 模式下由 AI 自动决策搜索"
- **AND** 用户无法手动控制搜索开关

#### Scenario: Agent 模式错误降级
- **WHEN** Agent 模式执行失败
- **THEN** 系统显示错误消息
- **AND** 建议用户切换到 Chat 模式
- **AND** 不自动切换模式 (尊重用户选择)

### Requirement: 模式状态管理
系统必须（SHALL）正确管理模式状态和会话数据。

#### Scenario: 模式状态保存
- **WHEN** 用户选择模式
- **THEN** 系统将模式保存到会话状态
- **AND** 使用 `cl.user_session.set("mode", mode_value)`
- **AND** 后续消息根据保存的模式处理

#### Scenario: 模式状态读取
- **WHEN** 处理用户消息时
- **THEN** 系统读取当前会话的模式
- **AND** 使用 `cl.user_session.get("mode", "chat")`
- **AND** 根据模式路由到相应的处理器

#### Scenario: 模式切换时历史清理
- **WHEN** 用户切换模式
- **THEN** 清除对话历史记录
- **AND** 清除搜索结果缓存
- **AND** 重置相关状态变量

#### Scenario: 会话结束清理
- **WHEN** 用户会话结束
- **THEN** 清理模式相关的所有状态
- **AND** 释放相关资源
- **AND** 不影响其他会话

### Requirement: 模式 UI 组件
系统必须（SHALL）提供清晰的 UI 组件展示和控制模式。

#### Scenario: 设置面板模式选择器
- **WHEN** 设置面板显示时
- **THEN** 包含模式选择器 (Select 组件)
- **AND** ID: "mode_selector"
- **AND** Label: "💬 对话模式"
- **AND** Options: ["Chat 模式", "Agent 模式"]

#### Scenario: 模式选择器交互
- **WHEN** 用户点击模式选择器
- **THEN** 显示模式选项列表
- **AND** 当前模式高亮显示
- **AND** 选择新模式后立即响应

#### Scenario: 模式指示器
- **WHEN** 用户查看界面
- **THEN** 可以清楚地看到当前处于什么模式
- **AND** 可以通过设置面板或状态栏查看
- **AND** 模式切换后指示器同步更新

#### Scenario: 搜索开关状态联动
- **WHEN** 处于 Agent 模式
- **THEN** 搜索开关显示为禁用
- **AND** 鼠标悬停显示提示信息
- **WHEN** 切换到 Chat 模式
- **THEN** 搜索开关恢复可用状态

### Requirement: 模式相关命令
系统必须（SHALL）支持通过命令查看和切换模式。

#### Scenario: 查看当前模式
- **WHEN** 用户发送 `/config` 命令
- **THEN** 显示当前模式信息
- **AND** 显示模式相关的配置 (如 Agent 最大迭代次数)

#### Scenario: 通过命令切换模式 (可选)
- **WHEN** 用户发送 `/mode chat` 或 `/mode agent` 命令
- **THEN** 系统切换到指定模式
- **AND** UI 选择器同步更新
- **AND** 发送确认消息

#### Scenario: 帮助命令更新
- **WHEN** 用户发送 `/help` 命令
- **THEN** 显示模式相关的帮助信息
- **AND** 说明两种模式的区别
- **AND** 说明如何切换模式

