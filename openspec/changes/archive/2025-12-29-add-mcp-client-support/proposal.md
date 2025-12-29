# Change: 添加 MCP Client 支持

## Why

当前系统虽然支持通过 LangChain Tools 集成工具（如搜索工具），但缺乏对 MCP (Model Context Protocol) 标准的支持。MCP 是一个标准化的协议，允许 AI 应用与外部服务进行交互。通过集成 MCP Client，系统可以：

1. **标准化工具集成**: 使用统一的 MCP 协议接入各种外部服务
2. **扩展能力**: 轻松接入高德地图、企业微信、金融数据等 MCP 服务器
3. **动态工具发现**: MCP 协议支持动态发现可用工具，无需硬编码
4. **更好的可维护性**: 统一的工具管理接口，便于维护和扩展

高德地图 MCP 服务器提供了丰富的地图相关功能（路径规划、地点搜索、天气查询等），这些能力可以显著增强 Agent 的地理信息处理能力。

## What Changes

### 新增功能
- **MCP Client 支持**: 实现 MCP Client，支持连接到 MCP 服务器
- **MCP 工具自动发现**: 自动发现 MCP 服务器提供的工具
- **MCP 工具集成**: 将 MCP 工具转换为 LangChain Tool，供 Agent 使用
- **高德地图集成**: 集成高德地图 MCP 服务器，提供地图相关功能
- **MCP 配置管理**: 支持通过配置文件管理多个 MCP 服务器

### 修改现有功能
- **Agent 工具系统**: 扩展 Agent 工具系统，支持 MCP 工具
- **工具注册机制**: 修改工具注册机制，支持动态添加 MCP 工具

### 核心特性
1. **MCP Client 实现**:
   - 支持 SSE (Server-Sent Events) 和 HTTP 两种连接方式
   - 实现工具列表查询
   - 实现工具调用
   - 支持异步操作

2. **工具转换**:
   - 将 MCP 工具定义转换为 LangChain Tool
   - 保持工具描述和参数的完整性
   - 支持工具调用的错误处理

3. **高德地图集成**:
   - 路径规划（驾车、步行、骑行、公交）
   - 地点搜索和详情查询
   - 地理编码和逆地理编码
   - 天气查询
   - IP 定位

## Impact

### 影响的规范
- **新增规范**: `mcp-client` - MCP Client 功能规范
- **修改规范**: `agent-mode` - 添加 MCP 工具支持

### 影响的代码
- **配置层** (新增): `src/config/mcp_config.py` - MCP 服务器配置管理
- **MCP 层** (新增): `src/mcp/` - MCP Client 实现
  - `src/mcp/client.py` - MCP Client 核心实现
  - `src/mcp/tool_adapter.py` - MCP 工具到 LangChain Tool 的适配器
  - `src/mcp/models.py` - MCP 数据模型
- **工具层** (修改): `src/agents/tools/` - 支持 MCP 工具注册
- **应用层** (修改): `app.py` - 初始化 MCP Client 并注册工具

### 用户体验变化
- **新增能力**: Agent 可以使用地图相关功能（路径规划、地点搜索等）
- **向后兼容**: 现有搜索工具功能不受影响
- **透明集成**: MCP 工具的使用方式与现有工具一致

### 技术依赖
- **MCP SDK**: 使用 Python MCP SDK (`mcp` 包)
- **HTTP/SSE 客户端**: 支持 HTTP 和 SSE 连接方式
- **LangChain Tools**: 继续使用 LangChain Tool 抽象

### 潜在风险
- **网络依赖**: MCP 服务器需要稳定的网络连接
- **API 限制**: 高德地图等外部服务可能有调用频率限制
- **错误处理**: 需要完善的错误处理和降级策略
- **配置复杂度**: 多个 MCP 服务器的配置管理可能增加复杂度

