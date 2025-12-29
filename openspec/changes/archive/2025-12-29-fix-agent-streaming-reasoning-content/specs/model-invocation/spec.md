## MODIFIED Requirements

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

