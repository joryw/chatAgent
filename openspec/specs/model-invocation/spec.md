# model-invocation Specification

## Purpose
TBD - created by archiving change add-model-invocation. Update Purpose after archive.
## Requirements
### Requirement: 模型提供商支持
系统必须（SHALL）通过统一接口支持多个LLM提供商，包括OpenAI、Anthropic和DeepSeek。

#### Scenario: OpenAI模型调用
- **WHEN** 用户请求使用OpenAI GPT-4生成响应
- **THEN** 系统使用配置的参数调用OpenAI API
- **AND** 返回生成的响应

#### Scenario: Anthropic模型调用
- **WHEN** 用户请求使用Anthropic Claude生成响应
- **THEN** 系统使用配置的参数调用Anthropic API
- **AND** 返回生成的响应

#### Scenario: DeepSeek模型调用
- **WHEN** 用户请求使用DeepSeek模型生成响应
- **THEN** 系统使用配置的参数调用DeepSeek API
- **AND** 返回生成的响应

#### Scenario: 模型切换
- **WHEN** 配置指定不同的模型提供商
- **THEN** 系统使用相应的提供商包装器
- **AND** 为应用层保持一致的接口

### Requirement: 模型配置
系统必须（SHALL）允许配置模型参数，包括模型名称、模型变体、temperature、max_tokens和top_p。

#### Scenario: 默认配置
- **WHEN** 未提供自定义参数
- **THEN** 系统使用默认值（temperature=0.7, max_tokens=2000, model_variant=deepseek-chat）
- **AND** 成功调用模型

#### Scenario: 自定义参数
- **WHEN** 用户指定自定义参数（temperature=0.3, max_tokens=500, model_variant=deepseek-reasoner）
- **THEN** 系统将这些参数应用到模型调用
- **AND** 遵守参数约束

#### Scenario: 无效参数
- **WHEN** 用户提供无效参数（temperature=2.0或负数令牌，或不支持的 model_variant）
- **THEN** 系统在调用前验证参数
- **AND** 抛出带有清晰消息的配置错误

### Requirement: 提示词管理
系统必须（SHALL）提供提示词模板化和格式化能力，用于构建模型输入。

#### Scenario: 系统和用户消息格式化
- **WHEN** 应用层提供系统指令和用户查询
- **THEN** 系统将它们格式化为正确的消息结构
- **AND** 维护基于角色的消息顺序

#### Scenario: 提示词模板渲染
- **WHEN** 使用带变量的提示词模板
- **THEN** 系统用实际值替换占位符
- **AND** 生成完整的模型提示词

#### Scenario: 令牌计数
- **WHEN** 准备提示词用于调用
- **THEN** 系统计算提示词中的令牌数
- **AND** 在接近上下文窗口限制时发出警告

### Requirement: 错误处理与弹性
系统必须（SHALL）实现健壮的错误处理，并为瞬态故障提供重试逻辑。

#### Scenario: 限流处理
- **WHEN** API返回限流错误（HTTP 429）
- **THEN** 系统等待retry-after时间
- **AND** 使用指数退避重试请求最多3次

#### Scenario: 认证错误
- **WHEN** API密钥无效或缺失
- **THEN** 系统立即抛出认证错误
- **AND** 不进行重试（非瞬态错误）

#### Scenario: 网络超时
- **WHEN** API请求超过超时阈值（30秒）
- **THEN** 系统取消请求
- **AND** 向调用者返回超时错误

#### Scenario: 通用API错误
- **WHEN** API返回意外错误
- **THEN** 系统记录错误详情
- **AND** 如果错误可能是瞬态的（5xx错误）则重试
- **AND** 对客户端错误（除429外的4xx）快速失败

### Requirement: 响应处理
系统必须（SHALL）在返回给应用层之前处理和验证模型响应。

#### Scenario: 成功响应
- **WHEN** 模型返回有效响应
- **THEN** 系统提取生成的文本
- **AND** 包含使用元数据（使用的令牌数、模型等）
- **AND** 返回结构化响应对象

#### Scenario: 空响应
- **WHEN** 模型返回空内容或null
- **THEN** 系统检测到空响应
- **AND** 抛出表明模型输出无效的错误

#### Scenario: 响应验证
- **WHEN** 从模型接收到响应
- **THEN** 系统验证响应结构
- **AND** 确保必需字段存在
- **AND** 记录任何异常以供调试

### Requirement: LangChain集成
系统必须（SHALL）与LangChain框架集成，用于模型抽象和管理，并正确处理 DeepSeek API 的特殊要求。

#### Scenario: LangChain模型包装器
- **WHEN** 通过系统调用模型
- **THEN** 系统使用LangChain的模型抽象
- **AND** 受益于内置特性（回调、缓存等）

#### Scenario: LangChain回调
- **WHEN** 模型调用正在进行中
- **THEN** 系统支持用于日志记录的LangChain回调
- **AND** 允许监控令牌使用和延迟

#### Scenario: DeepSeek Tool Calls 消息格式处理
- **WHEN** 使用 DeepSeek 模型进行 Agent 模式下的工具调用（function call）
- **THEN** 系统确保所有包含 `tool_calls` 的 assistant message 都包含 `reasoning_content` 字段
- **AND** 在消息历史中正确维护 `reasoning_content` 字段
- **AND** 在流式调用时正确处理消息格式
- **AND** 如果消息缺少 `reasoning_content`，系统自动添加默认值或使用消息的 `content` 字段

#### Scenario: LangGraph 流式调用消息处理
- **WHEN** 通过 LangGraph 进行流式调用时
- **THEN** 系统在 API 调用前验证并修复消息格式
- **AND** 确保消息历史中的所有 assistant message 都符合 DeepSeek API 要求
- **AND** 处理消息对象的不同格式（dict vs BaseMessage）
- **AND** 在检测到格式错误时自动修复并重试

#### Scenario: 消息格式错误恢复
- **WHEN** DeepSeek API 返回 `reasoning_content` 相关错误
- **THEN** 系统捕获错误并自动修复消息格式
- **AND** 重新发送修复后的请求
- **AND** 记录详细的错误和修复日志
- **AND** 如果自动修复失败，返回友好的错误消息

### Requirement: Chainlit界面集成
系统必须（SHALL）通过Chainlit界面提供交互式测试和验证能力,包括推理内容的流式展示和自动折叠。

#### Scenario: 对话式测试界面
- **WHEN** 用户通过Chainlit界面发送消息
- **THEN** 系统调用配置的模型生成响应
- **AND** 在界面上显示响应内容和元数据（令牌数、耗时等）

#### Scenario: 模型切换功能
- **WHEN** 用户在界面上选择不同的模型提供商
- **THEN** 系统切换到相应的模型
- **AND** 后续对话使用新选择的模型

#### Scenario: 参数调节功能
- **WHEN** 用户调整模型参数（temperature、max_tokens）
- **THEN** 系统应用新参数到模型调用
- **AND** 在界面上反馈参数更改状态

#### Scenario: 错误展示
- **WHEN** 模型调用发生错误
- **THEN** 系统在Chainlit界面上显示友好的错误消息
- **AND** 提供错误原因和解决建议

#### Scenario: 推理内容流式展示
- **WHEN** 使用支持推理的模型(如 DeepSeek Reasoner)生成响应
- **THEN** 系统创建展开的 Step 组件展示思考过程
- **AND** 实时流式显示思考内容的每个字符
- **AND** 使用清晰的视觉指示(如 "💭 思考中...")标识当前状态

#### Scenario: 思考内容自动折叠
- **WHEN** 模型完成思考并开始生成正式回答
- **THEN** 系统自动将思考内容折叠
- **AND** 更新视觉指示为完成状态(如 "💡 思考过程")
- **AND** 用户可以随时点击展开查看思考内容
- **AND** 确保折叠操作只执行一次,避免重复

#### Scenario: 正式回答流式输出
- **WHEN** 思考内容折叠后,模型继续生成正式回答
- **THEN** 系统在独立的消息框中流式显示回答内容
- **AND** 用户能够清晰区分思考过程和最终回答
- **AND** 保持流畅的阅读体验

#### Scenario: 思考过程异常处理
- **WHEN** 在思考内容展示过程中发生错误
- **THEN** 系统确保 Step 组件正确关闭
- **AND** 显示友好的错误提示
- **AND** 不影响后续的对话功能

### Requirement: DeepSeek 模型选择
系统必须（SHALL）支持用户在 DeepSeek 的不同模型变体之间进行选择，包括 deepseek-chat 和 deepseek-reasoner。

#### Scenario: 选择 deepseek-chat 模型
- **WHEN** 用户通过设置面板或命令选择 deepseek-chat 模型
- **THEN** 系统使用 deepseek-chat 模型进行后续对话
- **AND** 响应直接包含答案内容，无思考过程

#### Scenario: 选择 deepseek-reasoner 模型
- **WHEN** 用户通过设置面板或命令选择 deepseek-reasoner 模型
- **THEN** 系统使用 deepseek-reasoner 模型进行后续对话
- **AND** 响应包含思考过程和最终答案两部分

#### Scenario: 默认模型配置
- **WHEN** 用户未明确选择模型变体
- **THEN** 系统使用环境变量 DEEPSEEK_MODEL_VARIANT 指定的模型
- **AND** 如果环境变量未设置，默认使用 deepseek-chat

#### Scenario: 模型切换
- **WHEN** 用户在对话过程中切换模型
- **THEN** 系统清除对话历史
- **AND** 后续消息使用新选择的模型
- **AND** 显示模型切换成功的确认消息

### Requirement: 思考内容展示
当使用 deepseek-reasoner 模型时，系统必须（SHALL）在流式响应中展示模型的思考过程，并在开始输出正式答案时自动折叠思考内容。

#### Scenario: 流式展示思考过程
- **WHEN** deepseek-reasoner 模型开始生成响应
- **THEN** 系统在 UI 中创建可折叠的"思考中"区域
- **AND** 实时流式更新思考内容
- **AND** 使用特殊标识（如 💭 图标）区分思考内容

#### Scenario: 自动折叠思考内容
- **WHEN** 模型完成思考并开始输出正式答案
- **THEN** 系统自动折叠思考内容区域
- **AND** 将标题更新为"思考过程"
- **AND** 在新的消息区域开始显示正式答案

#### Scenario: 手动展开思考内容
- **WHEN** 用户点击已折叠的思考内容区域
- **THEN** 系统展开并显示完整的思考过程
- **AND** 用户可以查看模型的推理步骤

#### Scenario: 无思考内容的情况
- **WHEN** 使用 deepseek-chat 模型或 API 未返回思考内容
- **THEN** 系统不显示思考内容区域
- **AND** 直接显示模型的答案

### Requirement: 响应解析和处理
系统必须（SHALL）正确解析 deepseek-reasoner 模型的 API 响应，区分思考内容（reasoning_content）和正式答案（content）。

#### Scenario: 解析包含思考内容的响应
- **WHEN** API 返回包含 reasoning_content 字段的流式响应
- **THEN** 系统识别并提取思考内容
- **AND** 将思考内容标记为 "reasoning" 类型的 StreamChunk
- **AND** 将答案内容标记为 "answer" 类型的 StreamChunk

#### Scenario: 解析不包含思考内容的响应
- **WHEN** API 返回不包含 reasoning_content 字段的响应（deepseek-chat）
- **THEN** 系统将所有内容视为答案
- **AND** 生成 "answer" 类型的 StreamChunk
- **AND** 不创建思考内容区域

#### Scenario: 处理格式异常
- **WHEN** API 响应格式与预期不符
- **THEN** 系统记录警告日志
- **AND** 尝试降级处理（将全部内容作为答案）
- **AND** 不中断用户对话流程

### Requirement: 推理内容状态管理
系统必须（SHALL）可靠地管理推理内容的展示状态,确保状态转换的原子性和一致性。

#### Scenario: 状态标记跟踪
- **WHEN** 系统创建思考内容 Step 组件
- **THEN** 系统初始化状态为展开(expanded)
- **AND** 使用内部标记跟踪折叠状态
- **AND** 防止重复执行折叠操作

#### Scenario: 状态转换触发
- **WHEN** 系统接收到第一个正式回答 chunk
- **THEN** 系统立即触发思考内容折叠
- **AND** 同步更新所有相关的视觉指示
- **AND** 记录状态转换日志用于调试

#### Scenario: 生命周期管理
- **WHEN** 思考内容 Step 不再需要时
- **THEN** 系统正确关闭 Step 的上下文管理器
- **AND** 释放相关资源
- **AND** 确保在异常情况下也能正确清理

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

