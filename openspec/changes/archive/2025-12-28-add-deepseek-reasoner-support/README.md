# DeepSeek Reasoner 模型支持提案

## 概述

本提案为 chatAgent 项目添加 DeepSeek Reasoner 推理模型支持，并实现思考过程的流式展示功能。

## 文件说明

- **[proposal.md](./proposal.md)** - 变更提案：为什么需要这个功能，影响范围
- **[tasks.md](./tasks.md)** - 实现任务清单：详细的开发步骤
- **[design.md](./design.md)** - 设计文档：技术决策、架构设计、风险分析
- **[specs/model-invocation/spec.md](./specs/model-invocation/spec.md)** - 功能规范变更（delta）

## 主要功能

### 1. 模型选择
- 支持在 `deepseek-chat` 和 `deepseek-reasoner` 之间切换
- **推荐方式**: 通过 UI 设置面板的下拉菜单选择（与联网搜索控件类似）
- 只在使用 DeepSeek 提供商时显示选择控件
- 默认值可通过环境变量配置

### 2. 思考过程展示
- 流式显示 reasoner 模型的思考内容
- 自动折叠：当开始输出正式答案时，思考内容自动折叠
- 可手动展开查看完整推理过程
- 视觉上清晰区分思考和答案

## 使用场景

### 场景 1: 复杂推理任务
用户问："如果一个人从地球上跳起来，理论上最高能跳多高？"

**使用 deepseek-reasoner:**
```
💭 思考中... (可折叠)
├─ 需要考虑重力加速度...
├─ 计算人体肌肉的最大爆发力...
├─ 考虑空气阻力的影响...
└─ 综合计算得出结果...

💬 正式回答:
根据物理学原理，一个普通成年人...
```

### 场景 2: 普通对话
用户问："今天天气怎么样？"

**使用 deepseek-chat:**
```
💬 直接回答:
今天天气晴朗，温度适宜...
```

## 技术亮点

1. **UI 一致性**：与联网搜索控件采用相同的 UI 实现方式
2. **响应解析**：智能识别 API 响应中的 `reasoning_content` 字段
3. **流式更新**：实时更新思考内容，无延迟感
4. **优雅折叠**：使用 Chainlit Step 组件实现自动折叠效果
5. **条件显示**：只在 DeepSeek 提供商下显示模型选择控件
6. **向后兼容**：完全兼容现有的 deepseek-chat 使用方式

## 配置示例

```bash
# .env 文件
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_MODEL_VARIANT=deepseek-reasoner  # 或 deepseek-chat
```

## 使用方式

### 💡 推荐：通过 UI 设置面板

1. 首先确保使用 DeepSeek 提供商
2. 点击右上角 ⚙️ 图标打开设置面板
3. 在 "🤖 DeepSeek 模型" 下拉菜单中选择：
   - `deepseek-chat` - 标准对话模型
   - `deepseek-reasoner` - 推理模型（显示思考过程）
4. 选择后立即生效，无需重启

### 📝 配置文件方式

```bash
# .env 文件中设置默认模型
DEEPSEEK_MODEL_VARIANT=deepseek-reasoner  # 或 deepseek-chat
```

### 🔍 查看配置

```bash
# 查看当前配置
/config

# 查看帮助
/help
```

## 开发进度

详见 [tasks.md](./tasks.md) 中的任务清单。

## 验证

运行以下命令验证提案：
```bash
openspec validate add-deepseek-reasoner-support --strict
```

## 相关资源

- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [Chainlit Step 组件文档](https://docs.chainlit.io/concepts/step)
- [项目 model-invocation 规范](../../specs/model-invocation/spec.md)

