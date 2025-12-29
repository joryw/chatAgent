# Change: 为模型调用添加当前日期信息

## Why
模型在回答问题时需要知道当前的日期和时间，以便提供准确的时间相关答案。例如，当用户询问"今天是星期几？"或"现在是什么时候？"时，模型需要知道当前日期才能正确回答。

## What Changes
- 在所有模型调用时自动添加当前日期信息到系统消息中
- 日期格式：YYYY-MM-DD（例如：2024-12-26）
- 时间格式：HH:MM:SS（可选，用于更精确的时间信息）
- 支持所有模型包装器（OpenAI、Anthropic、DeepSeek）

## Impact
- Affected specs: model-invocation
- Affected code: 
  - `src/models/base.py` - 添加日期信息辅助方法
  - `src/models/openai_wrapper.py` - 在系统消息中添加日期
  - `src/models/anthropic_wrapper.py` - 在系统消息中添加日期
  - `src/models/deepseek_wrapper.py` - 在系统消息中添加日期

