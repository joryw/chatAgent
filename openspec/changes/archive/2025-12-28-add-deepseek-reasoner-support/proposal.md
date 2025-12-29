# Change: 添加 DeepSeek Reasoner 模型支持和思考过程展示

## Why

当前系统仅支持 DeepSeek 的基础对话模型（deepseek-chat），但 DeepSeek 还提供了推理模型（deepseek-reasoner），该模型会在生成最终答案前进行思考推理。为了提供更强大的推理能力和透明的思考过程，需要支持 deepseek-reasoner 模型，并在 UI 中实时展示其思考内容。

这个功能将：
1. 让用户能够选择使用 deepseek-chat 或 deepseek-reasoner 模型
2. 当使用 reasoner 模型时，流式展示其思考过程
3. 当模型开始正式回答时，自动折叠思考内容，保持界面整洁

## What Changes

- 扩展 DeepSeek 配置以支持多个模型选择（deepseek-chat, deepseek-reasoner）
- 修改 DeepSeekWrapper 以处理 reasoner 模型的特殊响应格式（思考内容 + 正式回答）
- 在 Chainlit UI 中添加模型选择功能（通过设置面板或命令）
- 实现思考内容的流式展示和自动折叠功能
- 解析 API 响应中的 reasoning_content 字段
- 在 UI 中区分显示思考内容和正式回答

## Impact

- **受影响的 specs**: model-invocation
- **受影响的代码**:
  - `src/config/model_config.py` - 添加模型选择配置
  - `src/models/deepseek_wrapper.py` - 支持 reasoner 模型的响应处理
  - `app.py` - UI 集成，添加模型选择和思考内容展示
  - 可能需要更新环境变量配置示例

## Breaking Changes

无破坏性变更。现有的 deepseek-chat 使用方式保持不变，新功能为可选增强。

