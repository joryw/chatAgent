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
系统必须（SHALL）允许配置模型参数，包括模型名称、temperature、max_tokens和top_p。

#### Scenario: 默认配置
- **WHEN** 未提供自定义参数
- **THEN** 系统使用默认值（temperature=0.7, max_tokens=2000）
- **AND** 成功调用模型

#### Scenario: 自定义参数
- **WHEN** 用户指定自定义参数（temperature=0.3, max_tokens=500）
- **THEN** 系统将这些参数应用到模型调用
- **AND** 遵守参数约束

#### Scenario: 无效参数
- **WHEN** 用户提供无效参数（temperature=2.0或负数令牌）
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
系统必须（SHALL）与LangChain框架集成，用于模型抽象和管理。

#### Scenario: LangChain模型包装器
- **WHEN** 通过系统调用模型
- **THEN** 系统使用LangChain的模型抽象
- **AND** 受益于内置特性（回调、缓存等）

#### Scenario: LangChain回调
- **WHEN** 模型调用正在进行中
- **THEN** 系统支持用于日志记录的LangChain回调
- **AND** 允许监控令牌使用和延迟

### Requirement: Chainlit界面集成
系统必须（SHALL）通过Chainlit界面提供交互式测试和验证能力。

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

