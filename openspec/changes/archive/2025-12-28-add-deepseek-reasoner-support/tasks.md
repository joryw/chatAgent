# 实现任务清单

## 1. 配置层扩展
- [x] 1.1 在 ModelConfig 中添加 model_variant 字段支持 deepseek-chat 和 deepseek-reasoner
- [x] 1.2 更新环境变量配置，添加 DEEPSEEK_MODEL_VARIANT 选项
- [x] 1.3 更新 .env.example 文件，添加新配置说明

## 2. 模型包装器更新
- [x] 2.1 修改 DeepSeekWrapper 的 generate_stream 方法，识别 reasoning_content 字段
- [x] 2.2 实现思考内容和正式回答的分离逻辑
- [x] 2.3 为不同类型的内容创建不同的 StreamChunk 类型（reasoning vs answer）
- [x] 2.4 确保向后兼容 deepseek-chat 模型

## 3. UI 集成（参照联网搜索实现方式）
- [x] 3.1 导入 Chainlit 的 Select 控件 (from chainlit.input_widget import Select)
- [x] 3.2 在 `@cl.on_chat_start` 中初始化 ChatSettings
  - 创建模型选择下拉菜单（deepseek-chat / deepseek-reasoner）
  - 设置默认值为当前配置的模型
  - 只在使用 DeepSeek 提供商时显示此控件
- [x] 3.3 实现 `@cl.on_settings_update` 回调处理模型切换
  - 处理模型选择变化
  - 更新 user_session 中的模型配置
  - 清除对话历史
  - 发送模型切换确认消息
- [x] 3.4 实现思考内容的流式展示（使用 cl.Step 可折叠组件）
- [x] 3.5 实现自动折叠逻辑：当开始输出正式回答时，折叠思考内容
- [x] 3.6 添加视觉标识区分思考内容和正式回答（💭 图标用于思考，💬 用于回答）
- [x] 3.7 更新欢迎消息，提示 UI 设置面板中的模型选择功能
- [x] 3.8 更新 /config 命令显示当前选择的模型

## 4. 命令系统扩展（保持与 UI 同步）
- [x] 4.1 保留 /switch 命令用于提供商切换（openai, anthropic, deepseek）
- [x] 4.2 添加说明：模型变体通过 UI 设置面板选择（推荐方式）
- [x] 4.3 确保命令与 UI 状态同步
- [x] 4.4 更新 /help 命令文档，说明 UI 设置面板的使用

## 5. 文档更新
- [x] 5.1 更新 README.md 添加 reasoner 模型使用说明
- [x] 5.2 更新快速开始文档
- [x] 5.3 添加思考内容展示功能的使用示例和截图

## 6. 测试验证
- [x] 6.1 测试 deepseek-chat 模型功能保持正常
- [x] 6.2 测试 deepseek-reasoner 模型的思考内容展示
- [x] 6.3 测试自动折叠功能
- [x] 6.4 测试 UI 下拉菜单的模型切换
  - 通过 UI 切换到 reasoner
  - 通过 UI 切换回 chat
  - 验证状态正确保持
- [x] 6.5 测试非 DeepSeek 提供商时不显示模型选择控件
- [x] 6.6 测试与其他设置控件（如联网搜索）的兼容性
- [x] 6.7 测试错误处理（API 错误、网络超时等）

---

## 实施状态

✅ **所有任务已完成** (2025-12-27)

详细实施报告请查看: [IMPLEMENTATION_COMPLETE.md](./IMPLEMENTATION_COMPLETE.md)

