# 实现任务清单

## 1. 规范定义
- [ ] 1.1 编写 agent-mode 规范 delta
- [ ] 1.2 编写 model-invocation 规范 delta
- [ ] 1.3 编写 web-search 规范 delta
- [ ] 1.4 验证规范格式 (`openspec validate add-agent-mode --strict`)

## 2. 基础架构
- [ ] 2.1 创建 `src/agents/` 目录结构
- [ ] 2.2 实现 Agent 基础类 (`src/agents/base.py`)
- [ ] 2.3 实现 ReAct Agent 控制器 (`src/agents/react_agent.py`)
- [ ] 2.4 定义 Agent 配置模型 (`src/config/agent_config.py`)

## 3. 工具层实现
- [ ] 3.1 创建 `src/agents/tools/` 目录
- [ ] 3.2 实现搜索工具包装器 (`src/agents/tools/search_tool.py`)
- [ ] 3.3 将 SearchService 适配为 LangChain Tool
- [ ] 3.4 实现工具执行结果格式化

## 4. LangChain Agent 集成
- [ ] 4.1 集成 LangChain ReAct Agent
- [ ] 4.2 配置 Agent 的 prompt 模板
- [ ] 4.3 实现 Agent 执行循环
- [ ] 4.4 处理 Agent 停止条件

## 5. 模式选择 UI
- [ ] 5.1 在 Chainlit 设置面板添加模式选择器
- [ ] 5.2 实现模式切换逻辑
- [ ] 5.3 保存用户选择的模式到会话状态
- [ ] 5.4 在欢迎消息中说明两种模式的区别

## 6. Agent 过程可视化
- [ ] 6.1 实现 Agent 思考过程的实时展示
- [ ] 6.2 实现工具调用的可视化 (显示搜索查询)
- [ ] 6.3 实现搜索结果的中间展示
- [ ] 6.4 实现最终回答的输出
- [ ] 6.5 使用 Chainlit Step 组件展示执行步骤

## 7. Chat 模式增强
- [ ] 7.1 保持现有 Chat 模式功能不变
- [ ] 7.2 确保搜索开关在 Chat 模式下正常工作
- [ ] 7.3 添加模式标识显示

## 8. Agent 模式实现
- [ ] 8.1 在 `app.py` 中添加 Agent 模式处理分支
- [ ] 8.2 实现 Agent 消息处理流程
- [ ] 8.3 处理 Agent 的流式输出
- [ ] 8.4 实现错误处理和降级策略

## 9. 流式输出支持
- [ ] 9.1 实现 Agent 思考过程的流式展示
- [ ] 9.2 实现工具调用的实时反馈
- [ ] 9.3 实现最终回答的流式输出
- [ ] 9.4 确保流式输出的性能优化

## 10. 配置管理
- [ ] 10.1 添加 Agent 模式相关环境变量
- [ ] 10.2 实现 Agent 配置验证
- [ ] 10.3 支持 Agent 参数调整 (max_iterations 等)
- [ ] 10.4 更新 env.example 文件

## 11. 错误处理
- [ ] 11.1 处理 Agent 执行超时
- [ ] 11.2 处理工具调用失败
- [ ] 11.3 处理 Agent 无限循环
- [ ] 11.4 实现 Agent 降级到 Chat 模式

## 12. 测试和验证
- [ ] 12.1 测试 Chat 模式的向后兼容性
- [ ] 12.2 测试 Agent 模式的基本功能
- [ ] 12.3 测试模式切换功能
- [ ] 12.4 测试多轮搜索场景
- [ ] 12.5 测试错误处理和降级

## 13. 文档更新
- [ ] 13.1 更新 README.md 添加 Agent 模式说明
- [ ] 13.2 创建 Agent 模式使用指南
- [ ] 13.3 添加配置示例
- [ ] 13.4 更新 QUICK_START.md
- [ ] 13.5 添加故障排查指南

## 14. 性能优化
- [ ] 14.1 优化 Agent 执行性能
- [ ] 14.2 实现工具调用缓存
- [ ] 14.3 优化流式输出性能
- [ ] 14.4 监控 token 消耗

## 15. 提交和归档
- [ ] 15.1 提交所有代码变更
- [ ] 15.2 运行最终验证
- [ ] 15.3 准备归档材料
- [ ] 15.4 执行 `openspec archive add-agent-mode`

