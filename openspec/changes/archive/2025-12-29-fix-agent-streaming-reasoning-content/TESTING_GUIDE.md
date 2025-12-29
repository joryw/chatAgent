# 测试指南：Agent 流式调用 reasoning_content 修复

## 单元测试结果

✅ **所有单元测试通过** (6/6)

测试脚本：`test_reasoning_content_fix.py`

### 测试覆盖

1. ✅ **dict 格式消息，包含 tool_calls** - 验证基本的消息处理逻辑
2. ✅ **dict 格式消息，tool_calls 但 content 为空** - 验证默认 reasoning_content
3. ✅ **BaseMessage 格式消息** - 验证 LangChain 消息格式支持
4. ✅ **消息历史中的多个 assistant message** - 验证消息历史处理
5. ✅ **消息索引 1（错误中提到的位置）** - 验证特定索引位置的处理
6. ✅ **已经包含 reasoning_content 的消息** - 验证不覆盖已有内容

## 手动测试步骤

### 前置条件

1. 确保环境变量配置正确：
   ```bash
   export DEEPSEEK_API_KEY="your-api-key"
   export DEEPSEEK_MODEL_VARIANT="deepseek-chat"  # 或 deepseek-reasoner
   ```

2. 启动应用：
   ```bash
   source venv/bin/activate
   chainlit run app.py -w
   ```

### 测试场景

#### 场景 1: Agent 模式下的简单搜索

1. 打开 Chainlit UI (通常是 http://localhost:8000)
2. 切换到 **Agent 模式**
3. 发送消息："帮我搜索一下 Python 的最新版本"
4. **预期结果**：
   - Agent 应该能够正常调用搜索工具
   - 不应该出现 `reasoning_content` 错误
   - 应该看到搜索过程和结果

#### 场景 2: 多轮对话中的工具调用

1. 在 Agent 模式下，先发送："搜索一下 Python"
2. 等待第一次搜索完成
3. 再发送："再搜索一下 Python 教程"
4. **预期结果**：
   - 第二次搜索应该能够正常执行
   - 消息历史中的 assistant message 应该都包含 reasoning_content
   - 不应该出现索引 1 的错误

#### 场景 3: 检查日志输出

在运行应用时，查看控制台日志，应该看到：

```
✅ [消息索引 X] 添加 reasoning_content (工具调用: N 个)
```

而不是：

```
❌ Missing `reasoning_content` field in the assistant message at message index 1
```

### 验证要点

- ✅ Agent 能够正常调用搜索工具
- ✅ 流式输出正常工作
- ✅ 没有 `reasoning_content` 相关错误
- ✅ 日志显示消息处理正常
- ✅ 多轮对话中消息历史正确处理

## 故障排除

如果仍然遇到 `reasoning_content` 错误：

1. **检查日志级别**：确保日志级别设置为 INFO 或 DEBUG
2. **检查消息格式**：查看日志中的消息处理信息
3. **检查 API 密钥**：确保 DeepSeek API 密钥正确配置
4. **检查模型配置**：确保使用的是 DeepSeek 模型

## 测试报告模板

```
测试日期: [日期]
测试人员: [姓名]
环境: [Python 版本, 依赖版本]

测试结果:
- [ ] 场景 1: Agent 模式下的简单搜索 - 通过/失败
- [ ] 场景 2: 多轮对话中的工具调用 - 通过/失败
- [ ] 场景 3: 检查日志输出 - 通过/失败

问题记录:
[如有问题，记录在此]

结论:
[测试结论]
```

