# web-search Specification Delta

## MODIFIED Requirements

### Requirement: SearXNG 集成
系统 SHALL 集成本地部署的 SearXNG 搜索引擎,提供稳定可靠的联网搜索能力。

#### Scenario: 使用本地 SearXNG 实例
- **WHEN** 系统启动时
- **THEN** 应当连接到本地部署的 SearXNG 实例
- **AND** 默认地址为 `http://localhost:8080`
- **AND** 验证实例的可用性和配置正确性

#### Scenario: 成功搜索
- **WHEN** 系统需要执行搜索且本地 SearXNG 服务可用
- **THEN** 系统向本地 SearXNG 实例发送搜索请求
- **AND** 接收并解析 JSON 格式的搜索结果(包括标题、URL、摘要)

#### Scenario: 搜索超时
- **WHEN** 搜索请求超过5秒未返回
- **THEN** 系统应当终止搜索请求
- **AND** 降级到无搜索模式继续对话
- **AND** 在界面显示搜索超时提示

#### Scenario: 服务不可用
- **WHEN** 本地 SearXNG 服务不可达或返回错误
- **THEN** 系统应当捕获错误
- **AND** 降级到无搜索模式继续对话
- **AND** 在界面显示搜索服务不可用提示
- **AND** 提示用户检查 SearXNG 部署状态

#### Scenario: 配置验证失败
- **WHEN** 本地 SearXNG 实例配置不正确(如未启用 JSON 格式)
- **THEN** 系统应当在启动时检测配置问题
- **AND** 显示具体的配置错误信息
- **AND** 提供配置修复建议和文档链接

### Requirement: 搜索配置
系统 SHALL 支持配置本地 SearXNG 实例相关参数。

#### Scenario: SearXNG 服务地址配置
- **WHEN** 系统启动时
- **THEN** 从环境变量读取 SearXNG 服务地址
- **AND** 默认使用本地地址 `http://localhost:8080`
- **AND** 验证服务地址的格式有效性
- **AND** 执行健康检查确认服务可用

#### Scenario: 搜索参数配置
- **WHEN** 系统初始化搜索配置时
- **THEN** 应当加载以下可配置参数:
  - 搜索结果数量(默认5条)
  - 搜索超时时间(默认5秒)
  - 搜索语言偏好(默认自动)
  - 结果摘要最大长度(默认200字符)

#### Scenario: 配置验证
- **WHEN** 加载搜索配置时
- **THEN** 系统应当验证配置值的有效性
- **AND** 对于无效配置使用默认值
- **AND** 记录配置加载日志
- **AND** 检查 SearXNG 实例的 JSON API 是否启用

#### Scenario: 部署指引
- **WHEN** 检测到 SearXNG 服务不可用
- **THEN** 系统应当显示部署指引信息
- **AND** 提供部署文档的链接
- **AND** 说明 Docker 部署的基本步骤

## ADDED Requirements

### Requirement: SearXNG 部署支持
系统 SHALL 提供完整的 SearXNG 本地部署指南和支持。

#### Scenario: 提供部署文档
- **WHEN** 用户需要部署 SearXNG
- **THEN** 系统应当提供详细的部署文档
- **AND** 文档包含 Docker Compose 配置示例
- **AND** 文档说明必要的 settings.yml 配置项
- **AND** 文档包含启动和验证步骤

#### Scenario: 配置模板提供
- **WHEN** 用户需要配置 SearXNG
- **THEN** 系统应当提供 docker-compose.yml 模板
- **AND** 提供 settings.yml 配置模板
- **AND** 模板包含所有必要的配置项
- **AND** 模板启用 JSON 格式和 API 支持

#### Scenario: 健康检查端点
- **WHEN** 用户需要验证 SearXNG 部署
- **THEN** 系统应当提供健康检查功能
- **AND** 验证服务是否可访问
- **AND** 验证 JSON API 是否可用
- **AND** 返回明确的检查结果和建议

### Requirement: 部署故障排查
系统 SHALL 提供 SearXNG 部署和配置的故障排查指导。

#### Scenario: 连接失败诊断
- **WHEN** 无法连接到 SearXNG 服务
- **THEN** 系统应当提示检查以下项目:
  - Docker 容器是否正在运行
  - 端口是否正确配置和开放
  - 网络连接是否正常
- **AND** 提供具体的检查命令

#### Scenario: 配置错误诊断
- **WHEN** SearXNG 配置不正确
- **THEN** 系统应当识别常见配置问题:
  - JSON 格式未启用
  - API 未启用
  - 端口配置错误
- **AND** 提供针对性的修复建议

#### Scenario: 服务重启指导
- **WHEN** 用户需要重启 SearXNG 服务
- **THEN** 系统文档应当提供重启命令
- **AND** 说明配置修改后的生效方式
- **AND** 提供验证服务恢复的方法

## REMOVED Requirements

无删除的需求。原有的搜索开关控制、搜索触发机制、搜索结果处理、搜索源展示、错误处理与降级等需求保持不变。

