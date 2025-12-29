# MCP Client 支持 - 设计文档

## Context

当前系统使用 LangChain Tools 集成工具（如搜索工具），但缺乏对 MCP (Model Context Protocol) 标准的支持。MCP 是一个标准化的协议，允许 AI 应用与外部服务进行交互。通过集成 MCP Client，系统可以标准化工具集成流程，并轻松接入各种外部服务。

高德地图 MCP 服务器提供了丰富的地图相关功能，这些能力可以显著增强 Agent 的地理信息处理能力。

## Goals / Non-Goals

### Goals
- 实现 MCP Client，支持连接到 MCP 服务器
- 自动发现 MCP 服务器提供的工具
- 将 MCP 工具转换为 LangChain Tool，供 Agent 使用
- 集成高德地图 MCP 服务器
- 支持通过配置管理多个 MCP 服务器

### Non-Goals
- 实现 MCP Server（只实现 Client）
- 支持所有 MCP 协议特性（先实现核心功能）
- 实现 MCP 资源（resources）支持（先实现工具支持）

## Decisions

### Decision: 使用 Python MCP SDK 或自定义实现
**选择**: 优先使用 Python MCP SDK (`mcp` 包)，如果 SDK 不满足需求或不存在，则实现自定义 MCP Client。

**理由**:
- 使用标准 SDK 可以减少维护成本
- 如果 SDK 不存在或不完善，自定义实现可以更好地控制行为
- 需要支持 SSE 和 HTTP 两种连接方式

**替代方案**:
- 完全自定义实现：更灵活但需要更多开发工作
- 只支持 HTTP：简单但可能不支持某些 MCP 服务器

### Decision: MCP 工具转换为 LangChain Tool
**选择**: 将 MCP 工具转换为 LangChain Tool，保持与现有工具系统的一致性。

**理由**:
- Agent 已经使用 LangChain Tool 抽象
- 统一工具接口便于管理和使用
- 不需要修改 Agent 核心逻辑

**实现方式**:
- 创建 `MCPToolAdapter` 类，将 MCP 工具定义转换为 LangChain Tool
- 实现工具调用包装器，将 LangChain Tool 调用转换为 MCP 工具调用

### Decision: MCP Client 初始化时机
**选择**: 在应用启动时初始化 MCP Client，并在 Agent 初始化时注册工具。

**理由**:
- 提前发现工具，避免运行时延迟
- 连接失败不影响应用启动（记录日志并跳过）
- Agent 初始化时工具已准备好

**实现方式**:
- 在 `app.py` 的 `@cl.on_chat_start` 中初始化 MCP Client
- 使用全局缓存避免重复初始化
- 在 Agent 初始化时获取已发现的工具

### Decision: 配置管理方式
**选择**: 优先从环境变量读取配置，支持从配置文件读取（可选）。

**理由**:
- 环境变量是当前项目的主要配置方式
- 支持配置文件可以提供更灵活的配置管理
- 保持与现有配置系统的一致性

**配置格式**:
```python
# 环境变量示例
MCP_SERVERS=amap-amap-sse,wecom
MCP_AMAP_URL=https://mcp.amap.com/sse?key=xxx
MCP_WECOM_COMMAND=uvx
MCP_WECOM_ARGS=wecom-bot-mcp-server
```

### Decision: 错误处理策略
**选择**: 连接失败时跳过该服务器，工具调用失败时返回错误信息给 Agent。

**理由**:
- 部分 MCP 服务器不可用不应影响整个系统
- Agent 可以根据错误信息决定下一步行动
- 保持系统的健壮性

**实现方式**:
- MCP Client 连接失败：记录警告日志，跳过该服务器
- 工具调用失败：捕获异常，返回错误信息给 Agent
- 实现重试机制（可配置）

## Risks / Trade-offs

### Risk: MCP SDK 可能不存在或不完善
**影响**: 需要实现自定义 MCP Client，增加开发工作量。

**缓解措施**:
- 先调研现有的 MCP SDK
- 如果 SDK 不存在，实现最小可用的 MCP Client
- 后续可以迁移到标准 SDK

### Risk: 网络依赖和 API 限制
**影响**: MCP 服务器不可用或达到调用限制时，工具无法使用。

**缓解措施**:
- 实现完善的错误处理和降级策略
- 支持配置超时和重试
- 记录详细的错误日志

### Risk: 配置复杂度增加
**影响**: 多个 MCP 服务器的配置管理可能变得复杂。

**缓解措施**:
- 使用清晰的配置命名约定
- 提供配置示例和文档
- 支持配置验证和错误提示

### Trade-off: 性能 vs 功能
**选择**: 优先实现核心功能，性能优化后续进行。

**理由**:
- 先验证功能可行性
- 性能优化可以在实际使用中根据需求进行

## Migration Plan

### Phase 1: 基础实现
1. 实现 MCP Client 核心功能
2. 实现工具发现和转换
3. 集成高德地图 MCP 服务器
4. 测试基本功能

### Phase 2: 完善和优化
1. 完善错误处理
2. 添加日志和监控
3. 性能优化
4. 文档完善

### Phase 3: 扩展支持
1. 支持更多 MCP 服务器
2. 支持 MCP 资源（resources）
3. 支持 MCP 提示（prompts）

## Open Questions

1. **MCP SDK 可用性**: Python MCP SDK 是否存在？功能是否完善？
2. **高德地图 API 限制**: 调用频率限制是多少？是否需要实现限流？
3. **工具命名冲突**: 如果多个 MCP 服务器提供同名工具，如何处理？
4. **工具版本管理**: MCP 工具定义可能变化，是否需要版本管理？

## Implementation Notes

### MCP Client 架构
```
src/mcp/
├── __init__.py
├── client.py          # MCP Client 核心实现
├── tool_adapter.py    # MCP 工具到 LangChain Tool 适配器
└── models.py          # MCP 数据模型
```

### 工具注册流程
1. 应用启动时初始化 MCP Client
2. 连接到配置的 MCP 服务器
3. 发现可用工具列表
4. 转换为 LangChain Tool
5. 在 Agent 初始化时注册工具

### 工具调用流程
1. Agent 决定调用工具
2. 识别工具类型（本地工具或 MCP 工具）
3. MCP 工具：通过 MCP Client 调用
4. 本地工具：直接执行
5. 返回结果给 Agent

