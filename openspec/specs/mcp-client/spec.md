# mcp-client Specification

## Purpose
TBD - created by archiving change add-mcp-client-support. Update Purpose after archive.
## Requirements
### Requirement: MCP Client 支持
系统必须（SHALL）提供 MCP (Model Context Protocol) Client 支持，允许连接到 MCP 服务器并发现、调用其提供的工具。

#### Scenario: MCP Client 初始化
- **WHEN** 应用启动时
- **THEN** 系统读取 MCP 服务器配置
- **AND** 连接到配置的 MCP 服务器
- **AND** 发现服务器提供的可用工具列表
- **AND** 将工具注册到 Agent 工具系统

#### Scenario: 支持 SSE 连接方式
- **WHEN** MCP 服务器配置为 SSE (Server-Sent Events) 连接
- **THEN** 系统使用 SSE 协议连接到服务器
- **AND** 建立持久连接
- **AND** 支持实时工具调用

#### Scenario: 支持 HTTP 连接方式
- **WHEN** MCP 服务器配置为 HTTP 连接
- **THEN** 系统使用 HTTP 协议连接到服务器
- **AND** 支持标准的 HTTP 请求/响应模式
- **AND** 支持工具调用

#### Scenario: 工具自动发现
- **WHEN** MCP Client 连接到服务器后
- **THEN** 系统自动查询服务器提供的工具列表
- **AND** 获取每个工具的名称、描述和参数定义
- **AND** 将工具信息转换为 LangChain Tool 格式

#### Scenario: MCP 工具调用
- **WHEN** Agent 决定使用 MCP 工具
- **THEN** 系统将工具调用请求发送到对应的 MCP 服务器
- **AND** 等待服务器响应
- **AND** 将响应结果返回给 Agent
- **AND** 在 UI 中展示工具调用过程

#### Scenario: MCP 连接错误处理
- **WHEN** MCP 服务器连接失败
- **THEN** 系统记录错误日志
- **AND** 跳过该服务器的工具注册
- **AND** 不影响其他 MCP 服务器和本地工具的使用
- **AND** Agent 可以继续使用其他可用工具

#### Scenario: MCP 工具调用错误处理
- **WHEN** MCP 工具调用失败
- **THEN** 系统捕获错误信息
- **AND** 将错误信息返回给 Agent
- **AND** Agent 可以根据错误信息决定下一步行动
- **AND** 在 UI 中展示错误信息

### Requirement: MCP 配置管理
系统必须（SHALL）支持通过配置文件管理多个 MCP 服务器。

#### Scenario: 读取 MCP 配置
- **WHEN** 应用启动时
- **THEN** 系统从环境变量或配置文件读取 MCP 服务器配置
- **AND** 支持配置多个 MCP 服务器
- **AND** 每个服务器配置包含连接 URL 和认证信息（如需要）

#### Scenario: 高德地图 MCP 配置
- **WHEN** 配置高德地图 MCP 服务器
- **THEN** 系统读取高德地图 MCP 服务器 URL
- **AND** 读取 API Key（如果配置在 URL 参数中）
- **AND** 连接到高德地图 MCP 服务器
- **AND** 发现并注册高德地图提供的工具

#### Scenario: 配置验证
- **WHEN** MCP 服务器配置无效或缺失
- **THEN** 系统跳过该服务器配置
- **AND** 记录警告日志
- **AND** 继续处理其他有效的 MCP 服务器配置

### Requirement: MCP 工具到 LangChain Tool 转换
系统必须（SHALL）将 MCP 工具定义转换为 LangChain Tool，以便 Agent 使用。

#### Scenario: 工具定义转换
- **WHEN** 系统发现 MCP 工具
- **THEN** 将 MCP 工具的名称、描述转换为 LangChain Tool
- **AND** 将 MCP 工具的参数定义转换为 LangChain Tool 的输入 schema
- **AND** 保持工具描述的完整性和准确性

#### Scenario: 工具参数映射
- **WHEN** Agent 调用 MCP 工具
- **THEN** 系统将 LangChain Tool 的参数映射到 MCP 工具的参数格式
- **AND** 验证参数类型和必需性
- **AND** 处理参数转换错误

#### Scenario: 工具返回值处理
- **WHEN** MCP 工具返回结果
- **THEN** 系统将 MCP 工具返回值格式化为 Agent 可理解的格式
- **AND** 保持返回值的完整信息
- **AND** 处理特殊数据类型（如 JSON、列表等）

### Requirement: 高德地图工具集成
系统必须（SHALL）集成高德地图 MCP 服务器，提供地图相关功能。

#### Scenario: 路径规划工具
- **WHEN** Agent 需要规划路径
- **THEN** Agent 可以调用高德地图路径规划工具
- **AND** 支持驾车、步行、骑行、公交等多种出行方式
- **AND** 返回路径规划结果（距离、时间、路线等）

#### Scenario: 地点搜索工具
- **WHEN** Agent 需要搜索地点
- **THEN** Agent 可以调用高德地图地点搜索工具
- **AND** 支持关键词搜索和周边搜索
- **AND** 返回地点列表和详细信息

#### Scenario: 地理编码工具
- **WHEN** Agent 需要将地址转换为坐标
- **THEN** Agent 可以调用高德地图地理编码工具
- **AND** 支持结构化地址解析
- **AND** 返回经纬度坐标

#### Scenario: 逆地理编码工具
- **WHEN** Agent 需要将坐标转换为地址
- **THEN** Agent 可以调用高德地图逆地理编码工具
- **AND** 支持坐标到地址的转换
- **AND** 返回结构化地址信息

#### Scenario: 天气查询工具
- **WHEN** Agent 需要查询天气信息
- **THEN** Agent 可以调用高德地图天气查询工具
- **AND** 支持按城市名称或行政区划代码查询
- **AND** 返回天气详情（温度、天气状况等）

#### Scenario: IP 定位工具
- **WHEN** Agent 需要根据 IP 地址定位
- **THEN** Agent 可以调用高德地图 IP 定位工具
- **AND** 支持 IP 地址到地理位置的转换
- **AND** 返回位置信息

### Requirement: Agent 工具系统扩展
系统必须（SHALL）扩展 Agent 工具系统，支持 MCP 工具与现有工具（如搜索工具）协同工作。

#### Scenario: 工具列表合并
- **WHEN** Agent 初始化时
- **THEN** 系统将本地工具（如搜索工具）和 MCP 工具合并
- **AND** 所有工具在 Agent 中可用
- **AND** Agent 可以自主选择使用哪个工具

#### Scenario: 工具调用路由
- **WHEN** Agent 决定调用工具
- **THEN** 系统识别工具类型（本地工具或 MCP 工具）
- **AND** 路由到对应的执行器
- **AND** 本地工具直接执行，MCP 工具通过 MCP Client 调用

#### Scenario: 工具描述展示
- **WHEN** Agent 展示可用工具时
- **THEN** 系统展示所有工具（包括 MCP 工具）的名称和描述
- **AND** 明确标识工具来源（本地工具或 MCP 工具）
- **AND** 提供工具使用示例（可选）

