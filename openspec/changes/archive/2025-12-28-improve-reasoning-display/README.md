# 改进推理内容流式展示和自动折叠体验

## 📋 提案概述

这个提案旨在优化 DeepSeek Reasoner 模型的思考过程展示体验,让用户能够更清晰地看到模型的推理过程,并在思考完成后自动折叠内容,保持界面整洁。

## 🎯 核心目标

1. **实时展示思考内容**: 在模型思考时,让用户能够看到流式输出的每个字
2. **自动折叠优化**: 当思考结束、开始正式回答时,优雅地将思考内容折叠
3. **清晰视觉反馈**: 使用明确的图标和状态提示,区分思考阶段和完成状态

## 📁 提案文件结构

```
improve-reasoning-display/
├── proposal.md          # 提案说明文档
├── design.md           # 技术设计文档
├── tasks.md            # 实施任务清单
├── specs/              # 规范变更
│   └── model-invocation/
│       └── spec.md     # model-invocation 规范的变更内容
└── README.md           # 本文件
```

## 🔄 变更内容

### 优化点 1: 明确展开状态
- **现状**: 思考内容创建时可能展示不明确
- **改进**: 在创建 Chainlit Step 时显式设置为展开状态
- **效果**: 用户能立即看到思考过程的流式输出

### 优化点 2: 精准折叠时机
- **现状**: 折叠时机可能不够及时
- **改进**: 在收到第一个正式回答 chunk 时立即触发折叠
- **效果**: 思考和回答的转换更加流畅自然

### 优化点 3: 清晰视觉指示
- **现状**: 状态指示可能不够明显
- **改进**: 使用不同的名称和图标
  - 思考中: "💭 思考中..."
  - 思考完成: "💡 思考过程"
- **效果**: 用户能清楚知道当前处于哪个阶段

### 优化点 4: 可靠状态管理
- **现状**: 可能存在重复折叠的问题
- **改进**: 使用 `_collapsed_already` 标记跟踪状态
- **效果**: 避免重复操作,确保状态一致性

## 🎨 用户体验流程

```
用户发送问题
    ↓
模型开始思考
    ↓
显示 "💭 思考中..." (展开状态)
    ↓
实时流式显示思考内容
    │ 用户可以看到每个字符...
    │ 思考推理的过程...
    │ 逻辑链条的构建...
    ↓
收到第一个回答 chunk
    ↓
自动折叠思考内容 → "💡 思考过程"
    ↓
流式显示正式回答
    ↓
完成 (用户可点击展开查看思考过程)
```

## 📊 技术实现亮点

### 1. 状态转换图

```
[创建 Step] → [展开显示] → [流式更新] → [触发折叠] → [显示回答]
     │             │             │             │             │
  collapsed=     持续接收      thinking_step   更新名称      独立消息框
    False      reasoning      .output +=    collapsed=     response_msg
              chunks           content        True
```

### 2. 核心代码逻辑

```python
# 创建思考 Step (展开状态)
thinking_step = cl.Step(name="💭 思考中...", type="tool")
await thinking_step.__aenter__()
thinking_step.collapsed = False  # 明确展开
await thinking_step.update()

# 流式更新思考内容
reasoning_content += chunk.content
thinking_step.output = reasoning_content
await thinking_step.update()

# 收到第一个回答时折叠
if not hasattr(thinking_step, '_collapsed_already'):
    thinking_step.name = "💡 思考过程"
    thinking_step.collapsed = True
    await thinking_step.update()
    await thinking_step.__aexit__(None, None, None)
    thinking_step._collapsed_already = True  # 防止重复
```

## ✅ 验证状态

- [x] OpenSpec 格式验证通过
- [x] 提案文档完整
- [x] 技术设计明确
- [x] 任务清单详细
- [x] 规范变更清晰

```bash
$ openspec validate improve-reasoning-display --strict
Change 'improve-reasoning-display' is valid ✓
```

## 📖 相关文档

- **提案说明**: [proposal.md](./proposal.md)
- **技术设计**: [design.md](./design.md)
- **实施任务**: [tasks.md](./tasks.md)
- **规范变更**: [specs/model-invocation/spec.md](./specs/model-invocation/spec.md)

## 🚀 下一步行动

1. **审查提案**: 团队审查提案内容,确认设计方案
2. **实施优化**: 按照 tasks.md 中的清单逐步实施
3. **测试验证**: 充分测试各种场景,确保体验改善
4. **部署上线**: 部署到生产环境,收集用户反馈

## 💡 使用建议

这个优化将使 DeepSeek Reasoner 模型的使用体验更加流畅和直观。建议在以下场景中特别关注:

- **复杂推理问题**: 需要模型深度思考的问题
- **多步骤推理**: 需要逻辑链条推导的任务
- **数学计算**: 需要展示计算过程的问题
- **分析决策**: 需要展示权衡过程的场景

---

**提案状态**: ✅ 已验证,待审批实施  
**创建日期**: 2025-12-27  
**OpenSpec 版本**: v1.0

