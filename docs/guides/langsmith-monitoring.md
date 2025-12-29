# LangSmith 监控使用指南

## 概述

LangSmith 是 LangChain 官方提供的监控和调试平台，可以自动追踪所有 LangChain 调用，提供详细的性能指标和调试信息。

## 功能特性

- 📊 **自动追踪**: 追踪所有模型调用、Agent 执行、工具调用
- 🔍 **调试支持**: 查看完整的调用链和中间状态
- 📈 **性能分析**: 分析延迟、token 使用、成本等指标
- 🎯 **项目组织**: 通过项目名称区分不同环境

## 快速开始

### 1. 注册 LangSmith 账号

1. 访问 https://smith.langchain.com/
2. 注册账号（免费 tier 可用）
3. 在设置页面获取 API 密钥

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# LangSmith 监控配置
LANGSMITH_API_KEY=your-api-key-here
LANGSMITH_PROJECT=chatagent-dev
```

**环境变量说明：**

- `LANGSMITH_API_KEY`: LangSmith API 密钥（必需，如果启用监控）
- `LANGSMITH_PROJECT`: 项目名称（可选，默认为 "chatagent-dev"）
- `LANGSMITH_API_URL`: 自定义 API 端点（可选，用于私有部署）

### 3. 重启应用

配置完成后，重启应用即可自动启用 LangSmith 监控。

## 追踪内容

启用 LangSmith 后，以下内容会被自动追踪：

### 模型调用追踪

- ✅ OpenAI GPT-4/GPT-3.5 调用
- ✅ Anthropic Claude 调用
- ✅ DeepSeek 模型调用
- ✅ 调用参数（temperature, max_tokens 等）
- ✅ 响应内容和元数据
- ✅ Token 使用情况
- ✅ 延迟时间

### Agent 执行追踪

- ✅ Agent 思考过程（reasoning）
- ✅ 工具调用决策
- ✅ 工具执行结果
- ✅ 多轮迭代过程
- ✅ 最终答案生成

### 工具调用追踪

- ✅ Web 搜索工具调用
- ✅ 搜索查询和结果
- ✅ 工具执行时间

## 项目组织

使用不同的项目名称来区分不同环境：

```bash
# 开发环境
LANGSMITH_PROJECT=chatagent-dev

# 测试环境
LANGSMITH_PROJECT=chatagent-test

# 生产环境
LANGSMITH_PROJECT=chatagent-prod
```

## 查看追踪数据

1. 登录 LangSmith 仪表板：https://smith.langchain.com/
2. 选择对应的项目
3. 查看追踪列表，包括：
   - 调用时间
   - 模型提供商
   - Token 使用
   - 延迟
   - 错误（如果有）

## 故障排查

### 监控未启用

**症状**: 在 LangSmith 仪表板中看不到追踪数据

**可能原因**:
1. `LANGSMITH_API_KEY` 未配置或无效
2. API 密钥格式错误
3. 网络连接问题

**解决方案**:
1. 检查 `.env` 文件中的 `LANGSMITH_API_KEY` 配置
2. 确认 API 密钥有效（从 LangSmith 设置页面重新获取）
3. 检查应用日志，查看是否有 LangSmith 初始化错误

### 初始化失败

**症状**: 应用启动时出现 LangSmith 相关警告

**日志示例**:
```
⚠️ LangSmith 初始化失败: ..., 继续执行（监控已禁用）
```

**解决方案**:
1. 检查 API 密钥是否正确
2. 确认网络连接正常
3. 如果使用自定义端点，检查 `LANGSMITH_API_URL` 配置

**注意**: 即使 LangSmith 初始化失败，应用仍会正常运行，只是监控功能被禁用。

### 性能影响

**症状**: 启用 LangSmith 后响应变慢

**说明**: LangSmith 调用是异步的，通常不会显著影响性能。如果确实有性能问题：

1. 检查网络延迟
2. 考虑使用私有部署的 LangSmith（如果可用）
3. 检查 LangSmith 服务状态

## 最佳实践

1. **环境隔离**: 使用不同的项目名称区分开发、测试、生产环境
2. **API 密钥安全**: 
   - 不要在代码中硬编码 API 密钥
   - 使用环境变量管理密钥
   - 不要将 `.env` 文件提交到版本控制
3. **定期审查**: 定期查看 LangSmith 仪表板，分析调用模式和性能
4. **成本追踪**: 使用 LangSmith 的成本追踪功能优化 API 调用

## 禁用监控

如果不需要监控，只需：

1. 从 `.env` 文件中删除或注释掉 `LANGSMITH_API_KEY`
2. 重启应用

应用会自动检测到未配置 API 密钥，禁用监控功能。

## 技术细节

### 集成方式

LangSmith 通过 LangChain 的回调机制集成：

1. **模型层**: 在 `get_langchain_llm()` 方法中添加 LangSmith 回调
2. **Agent 层**: 在 Agent 执行时传递回调配置
3. **自动追踪**: LangChain 自动追踪所有操作

### 代码位置

- 配置管理: `src/config/langsmith_config.py`
- 模型集成: `src/models/base.py` 和各个 wrapper
- Agent 集成: `src/agents/react_agent.py`

## 相关资源

- [LangSmith 官方文档](https://docs.smith.langchain.com/)
- [LangChain 回调文档](https://python.langchain.com/docs/modules/callbacks/)
- [项目配置文档](../README.md#configuration)

