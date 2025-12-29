# 实现任务清单

## 1. 规范定义
- [ ] 1.1 编写 model-invocation 规范 delta
- [ ] 1.2 验证规范格式 (`openspec validate add-langsmith-monitoring --strict`)

## 2. 依赖管理
- [ ] 2.1 在 `requirements.txt` 中添加 `langsmith` 依赖
- [ ] 2.2 更新 `env.example` 文件，添加 LangSmith 相关环境变量说明

## 3. 配置管理
- [ ] 3.1 创建 `src/config/langsmith_config.py` 配置文件
- [ ] 3.2 实现 LangSmith 配置模型（使用 Pydantic）
- [ ] 3.3 添加环境变量读取和验证逻辑
- [ ] 3.4 实现配置检查函数（检查是否启用 LangSmith）

## 4. LangSmith 初始化
- [ ] 4.1 在应用启动时初始化 LangSmith（如果配置了 API 密钥）
- [ ] 4.2 设置默认项目名称（从环境变量或使用默认值）
- [ ] 4.3 实现优雅降级（未配置时不影响功能）

## 5. 模型层集成
- [ ] 5.1 在 `src/models/base.py` 中添加 LangSmith 回调支持
- [ ] 5.2 修改 `get_langchain_llm()` 方法，添加 LangSmith 回调
- [ ] 5.3 更新各个模型 wrapper（OpenAI、Anthropic、DeepSeek）以支持回调
- [ ] 5.4 确保回调只在 LangSmith 启用时添加

## 6. Agent 层集成
- [ ] 6.1 在 `src/agents/react_agent.py` 中启用 LangSmith 追踪
- [ ] 6.2 配置 AgentExecutor 使用 LangSmith 回调
- [ ] 6.3 确保 Agent 执行过程完整追踪

## 7. 工具层集成（可选）
- [ ] 7.1 检查搜索工具是否需要特殊配置
- [ ] 7.2 确保工具调用也被 LangSmith 追踪

## 8. 错误处理
- [ ] 8.1 处理 LangSmith 初始化失败的情况
- [ ] 8.2 处理 LangSmith API 调用失败的情况（不应影响主流程）
- [ ] 8.3 添加适当的日志记录

## 9. 文档更新
- [ ] 9.1 更新 README.md，添加 LangSmith 配置说明
- [ ] 9.2 创建 LangSmith 使用指南文档
- [ ] 9.3 更新环境变量配置文档
- [ ] 9.4 添加故障排查指南

## 10. 测试和验证
- [ ] 10.1 测试未配置 LangSmith 时的行为（向后兼容）
- [ ] 10.2 测试配置 LangSmith 后的追踪功能
- [ ] 10.3 验证模型调用被正确追踪
- [ ] 10.4 验证 Agent 执行被正确追踪
- [ ] 10.5 检查 LangSmith 仪表板中的数据

## 11. 性能测试
- [ ] 11.1 测试启用 LangSmith 后的性能影响
- [ ] 11.2 确保异步调用不影响响应时间
- [ ] 11.3 验证错误处理不影响主流程

## 12. 提交和归档
- [ ] 12.1 提交所有代码变更
- [ ] 12.2 运行最终验证
- [ ] 12.3 准备归档材料
- [ ] 12.4 执行 `openspec archive add-langsmith-monitoring`

