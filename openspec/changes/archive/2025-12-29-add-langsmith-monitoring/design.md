# LangSmith 监控集成设计文档

## Context

### 背景
当前系统使用 LangChain 进行模型调用和 Agent 管理，但缺乏对调用过程的详细监控和追踪能力。LangSmith 是 LangChain 官方提供的监控平台，能够自动追踪所有 LangChain 操作并提供详细的性能指标和调试信息。

### 约束条件
- 必须保持向后兼容性（未配置 LangSmith 时功能不变）
- 必须使用 LangChain 的内置回调机制
- 监控调用不应影响主流程性能
- 需要安全地管理 API 密钥
- 需要考虑数据隐私和合规性

### 利益相关方
- **开发者**: 需要详细的调用追踪和调试信息
- **运维人员**: 需要监控系统性能和健康状况
- **最终用户**: 不应感知监控的存在（透明集成）

## Goals / Non-Goals

### Goals
1. ✅ 集成 LangSmith SDK，自动追踪所有 LangChain 调用
2. ✅ 支持通过环境变量可选启用（向后兼容）
3. ✅ 追踪模型调用、Agent 执行、工具调用等所有操作
4. ✅ 收集性能指标（延迟、token 使用、成本等）
5. ✅ 提供项目组织能力（区分不同环境）
6. ✅ 优雅处理错误（不影响主流程）

### Non-Goals
- ❌ 不实现自定义监控指标（使用 LangSmith 默认指标）
- ❌ 不实现本地监控存储（使用 LangSmith 云服务）
- ❌ 不实现监控数据的导出功能（LangSmith 已提供）
- ❌ 不实现监控告警功能（LangSmith 已提供）

## Decisions

### Decision 1: 使用 LangChain 回调机制

**选择**: 使用 LangChain 的 `CallbackHandler` 机制集成 LangSmith

**实现方式**:
```python
from langsmith import Client
from langchain_core.tracers import LangChainTracer

# 初始化 LangSmith 客户端
langsmith_client = Client(api_key=api_key)

# 创建回调处理器
tracer = LangChainTracer(
    project_name=project_name,
    client=langsmith_client
)

# 在模型调用时添加回调
llm = ChatOpenAI(callbacks=[tracer])
```

**理由**:
- LangChain 原生支持，无需额外适配
- 自动追踪所有 LangChain 操作
- 支持异步调用，性能影响小
- 与 LangChain 版本兼容性好

**替代方案**:
- **手动日志记录**: 需要大量代码，容易遗漏
- **AOP 切面编程**: 过度复杂，不符合 Python 生态
- **中间件模式**: LangChain 已提供回调机制，无需重复实现

**决策**: 使用 LangChain 回调机制，这是最标准和可靠的方式

### Decision 2: 配置管理方式

**选择**: 使用环境变量 + Pydantic 配置模型

**实现方式**:
```python
# src/config/langsmith_config.py
from pydantic import BaseModel, Field
import os

class LangSmithConfig(BaseModel):
    """LangSmith 配置"""
    enabled: bool = Field(default=False)
    api_key: Optional[str] = Field(default=None)
    project: str = Field(default="chatagent-dev")
    api_url: Optional[str] = Field(default=None)  # 可选，用于自定义端点
    
    @classmethod
    def from_env(cls) -> "LangSmithConfig":
        """从环境变量加载配置"""
        api_key = os.getenv("LANGSMITH_API_KEY")
        enabled = api_key is not None
        
        return cls(
            enabled=enabled,
            api_key=api_key,
            project=os.getenv("LANGSMITH_PROJECT", "chatagent-dev"),
            api_url=os.getenv("LANGSMITH_API_URL"),
        )
    
    def get_tracer(self) -> Optional[LangChainTracer]:
        """获取 LangSmith 追踪器（如果启用）"""
        if not self.enabled or not self.api_key:
            return None
        
        client = Client(api_key=self.api_key, api_url=self.api_url)
        return LangChainTracer(project_name=self.project, client=client)
```

**理由**:
- 符合项目现有的配置管理模式
- 使用 Pydantic 进行类型验证
- 支持环境变量覆盖
- 提供清晰的启用/禁用逻辑

**替代方案**:
- **配置文件**: 需要额外文件，增加复杂度
- **命令行参数**: 不适合 Chainlit 应用
- **数据库存储**: 过度设计，配置是静态的

**决策**: 使用环境变量 + Pydantic，简洁且符合项目规范

### Decision 3: 集成点选择

**选择**: 在模型包装器层和 Agent 层集成

**架构**:
```
app.py (应用层)
  ↓
src/models/base.py (模型包装器层)
  ↓ get_langchain_llm() → 添加 LangSmith 回调
LangChain LLM
  ↓
src/agents/react_agent.py (Agent 层)
  ↓ AgentExecutor → 添加 LangSmith 回调
LangChain Agent
```

**实现位置**:
1. **模型层**: 在 `BaseModelWrapper.get_langchain_llm()` 中添加回调
2. **Agent 层**: 在 `ReActAgent.__init__()` 中配置 AgentExecutor 回调

**理由**:
- 在统一入口添加回调，避免重复代码
- 模型层集成确保所有模型调用都被追踪
- Agent 层集成确保 Agent 执行过程被追踪
- 工具调用通过 Agent 自动追踪

**替代方案**:
- **仅在应用层集成**: 可能遗漏某些调用路径
- **在每个 wrapper 中单独集成**: 代码重复，难以维护

**决策**: 在模型包装器层和 Agent 层统一集成，确保完整覆盖

### Decision 4: 错误处理策略

**策略**:
1. **初始化失败**: 记录警告日志，禁用 LangSmith，不影响主流程
2. **API 调用失败**: 捕获异常，记录错误日志，继续执行主流程
3. **配置缺失**: 静默禁用，不输出错误（这是正常情况）

**实现**:
```python
def get_langsmith_tracer() -> Optional[LangChainTracer]:
    """获取 LangSmith 追踪器，失败时返回 None"""
    try:
        config = LangSmithConfig.from_env()
        if not config.enabled:
            return None
        
        tracer = config.get_tracer()
        logger.info("✅ LangSmith 监控已启用")
        return tracer
    except Exception as e:
        logger.warning(f"⚠️ LangSmith 初始化失败: {e}，继续执行（监控已禁用）")
        return None
```

**理由**:
- 监控是辅助功能，不应影响核心功能
- 优雅降级，保证系统可用性
- 提供足够的日志信息用于调试

### Decision 5: 项目命名策略

**选择**: 使用环境变量 `LANGSMITH_PROJECT` 指定项目名称

**默认值**: `chatagent-dev`（开发环境）

**建议命名**:
- 开发环境: `chatagent-dev`
- 测试环境: `chatagent-test`
- 生产环境: `chatagent-prod`

**理由**:
- 便于区分不同环境的监控数据
- 支持多环境部署
- 提供合理的默认值

## Risks / Trade-offs

### Risk 1: API 密钥泄露
**风险**: LangSmith API 密钥可能被泄露

**影响**: 
- 未授权访问监控数据
- 可能产生额外费用

**缓解措施**:
1. ✅ 在文档中明确说明密钥管理最佳实践
2. ✅ 使用环境变量，不硬编码密钥
3. ✅ 在 `.gitignore` 中确保 `.env` 不被提交
4. ✅ 建议使用密钥管理服务（如 AWS Secrets Manager）

### Risk 2: 性能影响
**风险**: LangSmith 调用可能影响响应时间

**影响**:
- 用户感知的延迟增加
- 系统吞吐量下降

**缓解措施**:
1. ✅ LangSmith 调用是异步的，影响最小
2. ✅ 使用后台线程发送数据
3. ✅ 进行性能测试，验证影响可接受
4. ✅ 如果影响过大，可以考虑批量发送

### Risk 3: 数据隐私
**风险**: 调用数据发送到 LangSmith 服务

**影响**:
- 可能包含敏感信息
- 需要符合数据保护法规

**缓解措施**:
1. ✅ 在文档中说明数据流向
2. ✅ 建议敏感场景禁用 LangSmith
3. ✅ 使用 LangSmith 的数据过滤功能（如果可用）
4. ✅ 考虑支持本地部署的 LangSmith（如果未来需要）

### Trade-off 1: 功能完整性 vs 复杂度
**权衡**: 完整集成 vs 最小化代码变更

**决策**: 
- 优先保证功能完整性（追踪所有调用）
- 使用 LangChain 回调机制，最小化代码变更
- 在统一入口集成，避免代码重复

### Trade-off 2: 实时性 vs 性能
**权衡**: 实时发送监控数据 vs 批量发送

**决策**:
- 使用 LangSmith SDK 的默认行为（通常是异步实时发送）
- 如果性能成为问题，可以考虑批量发送（未来优化）

## Migration Plan

### 阶段 1: 准备阶段（不影响现有功能）
1. 添加 `langsmith` 依赖到 `requirements.txt`
2. 创建配置模块 `src/config/langsmith_config.py`
3. 实现配置读取和验证逻辑
4. 更新环境变量文档

### 阶段 2: 集成阶段（可选功能）
1. 在模型包装器中添加 LangSmith 回调支持
2. 在 Agent 层添加 LangSmith 追踪
3. 实现优雅降级（未配置时禁用）
4. 添加错误处理和日志

### 阶段 3: 测试和文档
1. 编写使用文档和配置指南
2. 进行功能测试和性能测试
3. 验证向后兼容性
4. 更新 README 和相关文档

### 回滚计划
如果 LangSmith 集成出现问题:
1. 移除环境变量 `LANGSMITH_API_KEY` 即可禁用
2. 代码会自动降级，不影响主功能
3. 如果需要完全移除，可以回滚相关代码变更

### 数据迁移
无需数据迁移。LangSmith 监控是新增功能，不涉及现有数据。

## Open Questions

### Q1: 是否需要支持自定义 LangSmith 端点？
**状态**: 已解决  
**决策**: 支持通过 `LANGSMITH_API_URL` 环境变量自定义端点  
**原因**: 某些企业可能需要使用私有部署的 LangSmith

### Q2: 是否需要过滤敏感信息？
**状态**: 待讨论  
**倾向**: 第一版不实现，在文档中说明  
**原因**: LangSmith 可能已提供相关功能，需要进一步调研

### Q3: 是否需要支持多个项目名称（根据用户或会话）？
**状态**: 待讨论  
**倾向**: 第一版不支持，使用统一项目名称  
**原因**: 简化实现，未来可以根据需要扩展

### Q4: 是否需要监控工具调用（如搜索）的详细信息？
**状态**: 已解决  
**决策**: LangSmith 会自动追踪工具调用  
**原因**: LangChain 回调机制会自动处理

### Q5: 性能影响是否可接受？
**状态**: 需要测试验证  
**计划**: 在实现后进行性能测试  
**阈值**: 响应时间增加 < 100ms 可接受

