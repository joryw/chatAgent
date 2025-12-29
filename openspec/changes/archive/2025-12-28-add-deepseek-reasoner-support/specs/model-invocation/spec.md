## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Chainlit界面集成
系统必须（SHALL）通过Chainlit界面提供交互式测试和验证能力，包括模型选择和思考内容展示。

#### Scenario: 对话式测试界面
- **WHEN** 用户通过Chainlit界面发送消息
- **THEN** 系统调用配置的模型生成响应
- **AND** 在界面上显示响应内容和元数据（令牌数、耗时等）
- **AND** 如果使用 reasoner 模型，展示思考过程

#### Scenario: 模型选择功能
- **WHEN** 用户在设置面板中选择模型（deepseek-chat 或 deepseek-reasoner）
- **THEN** 系统切换到相应的模型
- **AND** 后续对话使用新选择的模型
- **AND** 在界面上显示当前使用的模型

#### Scenario: 思考内容的视觉呈现
- **WHEN** deepseek-reasoner 模型生成包含思考内容的响应
- **THEN** 系统使用可折叠的 Step 组件展示思考内容
- **AND** 使用不同的视觉样式（图标、颜色）区分思考和答案
- **AND** 提供流畅的折叠/展开动画

#### Scenario: 参数调节功能
- **WHEN** 用户调整模型参数（temperature、max_tokens）
- **THEN** 系统应用新参数到模型调用
- **AND** 在界面上反馈参数更改状态

#### Scenario: 错误展示
- **WHEN** 模型调用发生错误
- **THEN** 系统在Chainlit界面上显示友好的错误消息
- **AND** 提供错误原因和解决建议

