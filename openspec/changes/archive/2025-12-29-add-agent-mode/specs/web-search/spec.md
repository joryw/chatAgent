# web-search 规范变更

## MODIFIED Requirements

### Requirement: 搜索服务接口
系统必须（SHALL）提供灵活的搜索服务接口,支持在 Chat 模式和 Agent 模式下使用。

#### Scenario: Chat 模式搜索
- **WHEN** Chat 模式下启用搜索并用户发送消息
- **THEN** 系统使用用户的原始消息作为搜索查询
- **AND** 将搜索结果注入到模型提示中
- **AND** 模型基于搜索结果生成回答

#### Scenario: Agent 工具调用搜索
- **WHEN** Agent 模式下 Agent 决定使用搜索工具
- **THEN** Agent 生成优化的搜索查询
- **AND** 搜索服务执行查询并返回结果
- **AND** 结果返回给 Agent 而非直接注入提示

#### Scenario: 搜索结果格式化
- **WHEN** 搜索服务返回结果
- **THEN** 对于 Chat 模式,格式化为带编号的列表注入提示
- **AND** 对于 Agent 模式,格式化为紧凑的文本返回给工具
- **AND** 两种格式都包含标题、URL 和摘要

#### Scenario: 搜索查询优化
- **WHEN** Agent 生成搜索查询
- **THEN** 查询更加具体和针对性
- **AND** 可能与用户原始问题不同
- **AND** 旨在获取最相关的信息

### Requirement: 搜索工具适配
系统必须（SHALL）提供 SearchService 的工具适配器,使其可以作为 LangChain Tool 使用。

#### Scenario: 工具接口实现
- **WHEN** 创建 SearchTool 实例
- **THEN** 工具包装 SearchService 的功能
- **AND** 实现 LangChain BaseTool 接口
- **AND** 定义工具的名称、描述和输入 schema

#### Scenario: 工具同步调用
- **WHEN** Agent 同步调用搜索工具
- **THEN** 工具使用 SearchService 的同步方法
- **AND** 返回格式化的搜索结果字符串
- **AND** 处理并返回错误信息

#### Scenario: 工具异步调用
- **WHEN** Agent 异步调用搜索工具
- **THEN** 工具使用 SearchService 的异步方法
- **AND** 返回格式化的搜索结果字符串
- **AND** 支持并发调用

#### Scenario: 工具结果限制
- **WHEN** 工具返回搜索结果
- **THEN** 限制结果数量 (最多 5 条)
- **AND** 限制每条结果的摘要长度 (最多 200 字符)
- **AND** 保持结果的可读性和相关性

## MODIFIED Requirements

### Requirement: 搜索开关控制
系统必须（SHALL）在 Chat 模式下提供搜索开关,在 Agent 模式下禁用开关。

#### Scenario: Chat 模式搜索开关
- **WHEN** 系统处于 Chat 模式
- **THEN** 搜索开关正常可用
- **AND** 用户可以通过 UI 或命令控制
- **AND** 功能与现有实现完全一致

#### Scenario: Agent 模式搜索开关
- **WHEN** 系统处于 Agent 模式
- **THEN** 搜索开关显示为禁用状态
- **AND** 用户无法点击或切换
- **AND** 显示说明: "Agent 模式下由 AI 自动决策搜索"

#### Scenario: 模式切换时开关状态
- **WHEN** 用户从 Agent 模式切换到 Chat 模式
- **THEN** 搜索开关恢复可用状态
- **AND** 开关状态恢复为之前的设置或默认关闭
- **WHEN** 用户从 Chat 模式切换到 Agent 模式
- **THEN** 搜索开关变为禁用状态
- **AND** 保存当前开关状态以便切换回 Chat 模式时恢复

## ADDED Requirements

### Requirement: 搜索结果缓存
系统必须（SHALL）在 Agent 模式下缓存搜索结果,避免重复搜索相同查询。

#### Scenario: 缓存搜索结果
- **WHEN** Agent 执行搜索并获得结果
- **THEN** 将查询和结果缓存到会话状态
- **AND** 使用查询文本作为缓存键
- **AND** 缓存在当前会话内有效

#### Scenario: 使用缓存结果
- **WHEN** Agent 尝试搜索已缓存的查询
- **THEN** 直接返回缓存的结果
- **AND** 不执行实际的搜索请求
- **AND** 在日志中记录缓存命中

#### Scenario: 缓存过期
- **WHEN** 用户会话结束
- **THEN** 清除所有缓存的搜索结果
- **AND** 新会话重新开始缓存
- **AND** 不跨会话共享缓存

#### Scenario: 缓存大小限制
- **WHEN** 缓存的查询数量超过限制 (如 20 个)
- **THEN** 使用 LRU 策略删除最久未使用的缓存
- **AND** 保持缓存大小在限制内
- **AND** 防止内存过度使用

### Requirement: 搜索工具描述
系统必须（SHALL）提供清晰的工具描述,指导 Agent 何时以及如何使用搜索。

#### Scenario: 工具名称定义
- **WHEN** 定义搜索工具
- **THEN** 工具名称为 "web_search"
- **AND** 名称清晰表明其功能
- **AND** 符合 LangChain 工具命名规范

#### Scenario: 工具描述定义
- **WHEN** 定义搜索工具描述
- **THEN** 描述说明: "搜索互联网获取实时信息。当需要了解最新事件、实时数据、当前新闻或验证信息时使用此工具。"
- **AND** 明确说明使用场景
- **AND** 帮助 Agent 做出正确决策

#### Scenario: 工具输入说明
- **WHEN** 定义工具输入 schema
- **THEN** 输入参数为 query (str)
- **AND** 参数描述: "搜索查询关键词,应该具体、清晰、针对性强"
- **AND** 提供输入示例和最佳实践

#### Scenario: 工具使用示例
- **WHEN** Agent 需要使用搜索工具
- **THEN** Prompt 中包含使用示例
- **AND** 示例展示如何构造好的搜索查询
- **AND** 示例展示如何解读搜索结果

### Requirement: 搜索结果引用
系统必须（SHALL）在 Agent 模式下支持搜索结果的引用标记。

#### Scenario: 结果编号分配
- **WHEN** 搜索工具返回结果给 Agent
- **THEN** 每个结果分配唯一编号 (1, 2, 3...)
- **AND** 编号在工具输出中明确标注
- **AND** Agent 可以在回答中引用这些编号

#### Scenario: Agent 引用结果
- **WHEN** Agent 在回答中引用搜索结果
- **THEN** Agent 使用 [数字] 格式引用
- **AND** 系统识别并处理这些引用
- **AND** 将引用转换为可点击链接 (与 Chat 模式一致)

#### Scenario: 引用列表生成
- **WHEN** Agent 回答包含引用
- **THEN** 在回答末尾添加 "参考文献" 部分
- **AND** 列出所有使用的搜索来源
- **AND** 格式与 Chat 模式保持一致

#### Scenario: 无引用处理
- **WHEN** Agent 回答未使用搜索结果
- **THEN** 不添加引用列表
- **AND** 回答中不包含引用标记
- **AND** 用户可以看到 Agent 基于已有知识回答

