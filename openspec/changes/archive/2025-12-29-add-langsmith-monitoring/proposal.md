# Change: 接入 LangSmith 监控

## Why

当前系统缺乏对模型调用和 Agent 执行的详细监控能力，这导致以下问题：

1. **缺乏可观测性**: 无法追踪每次模型调用的详细信息（token 使用、延迟、成本等）
2. **难以调试**: 当出现问题时，无法查看完整的调用链和中间状态
3. **性能分析困难**: 无法分析哪些调用耗时较长，哪些消耗了更多 token
4. **成本追踪缺失**: 无法准确追踪和优化 API 调用成本
5. **生产环境监控不足**: 在生产环境中缺乏对系统健康状况的实时监控

LangSmith 是 LangChain 官方提供的监控和调试平台，能够：
- 自动追踪所有 LangChain 调用（模型、Agent、工具等）
- 提供详细的调用链视图和性能指标
- 支持调试、测试和评估工作流
- 提供成本追踪和优化建议

接入 LangSmith 将显著提升系统的可观测性和可维护性。

## What Changes

### 新增功能
- **LangSmith 集成**: 集成 LangSmith SDK，自动追踪所有 LangChain 调用
- **环境变量配置**: 添加 LangSmith API 密钥和项目名称配置
- **可选启用**: 通过环境变量控制是否启用 LangSmith 监控（不影响现有功能）
- **调用追踪**: 自动追踪模型调用、Agent 执行、工具调用等所有操作
- **性能指标收集**: 收集延迟、token 使用、成本等关键指标

### 修改现有功能
- **LangChain 回调配置**: 在模型包装器中添加 LangSmith 回调支持
- **Agent 执行追踪**: 在 Agent 执行时启用 LangSmith 追踪
- **配置管理**: 扩展配置系统以支持 LangSmith 相关配置

### 核心特性
1. **自动追踪**:
   - 所有通过 LangChain 的模型调用自动被追踪
   - Agent 执行过程完整记录
   - 工具调用（如搜索）也被追踪

2. **可选启用**:
   - 通过环境变量 `LANGSMITH_API_KEY` 控制是否启用
   - 未配置时不影响现有功能（向后兼容）

3. **项目组织**:
   - 支持通过 `LANGSMITH_PROJECT` 环境变量指定项目名称
   - 便于区分不同环境（开发、测试、生产）

## Impact

### 影响的规范
- **修改规范**: `model-invocation` - 添加 LangSmith 监控要求

### 影响的代码
- **配置层**: `src/config/model_config.py` - 添加 LangSmith 配置
- **模型层**: `src/models/base.py` 和各个 wrapper - 添加 LangSmith 回调
- **Agent 层**: `src/agents/react_agent.py` - 启用 LangSmith 追踪
- **应用层**: `app.py` - 初始化 LangSmith（如果需要）

### 用户体验变化
- **向后兼容**: 未配置 LangSmith 时功能完全不变
- **透明集成**: 用户无需感知监控的存在（除非查看 LangSmith 仪表板）
- **性能影响**: 监控调用是异步的，对用户体验影响最小

### 技术依赖
- **LangSmith SDK**: 需要安装 `langsmith` 包
- **LangChain 集成**: 利用 LangChain 的内置回调机制
- **环境变量**: 需要配置 `LANGSMITH_API_KEY` 和可选的 `LANGSMITH_PROJECT`

### 潜在风险
- **API 密钥管理**: 需要安全地管理 LangSmith API 密钥
- **性能开销**: 虽然异步，但仍可能有轻微的性能影响
- **数据隐私**: 调用数据会发送到 LangSmith 服务，需要考虑隐私合规

