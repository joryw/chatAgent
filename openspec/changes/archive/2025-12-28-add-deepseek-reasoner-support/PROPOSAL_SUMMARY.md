# 提案总结：DeepSeek Reasoner 模型支持

## ✅ 提案状态

**Change ID**: `add-deepseek-reasoner-support`  
**验证状态**: ✅ 通过 (strict mode)  
**创建日期**: 2025-12-27

## 📋 核心功能

### 1. 模型选择功能
支持用户在两种 DeepSeek 模型之间选择：
- **deepseek-chat**: 标准对话模型，直接生成答案
- **deepseek-reasoner**: 推理模型，先思考再回答

**选择方式**:
- UI 设置面板下拉菜单（推荐）
- 命令行：`/switch deepseek-reasoner`
- 环境变量：`DEEPSEEK_MODEL_VARIANT=deepseek-reasoner`

### 2. 思考过程展示
当使用 reasoner 模型时：
1. **流式展示**：实时显示模型的思考过程
2. **自动折叠**：开始输出答案时，思考内容自动折叠
3. **手动展开**：用户可点击查看完整推理过程
4. **视觉区分**：使用图标和样式区分思考与答案

## 📊 技术架构

### 响应处理流程

```
DeepSeek API 响应
    ↓
DeepSeekWrapper 解析
    ├─ reasoning_content → StreamChunk(type="reasoning")
    └─ content → StreamChunk(type="answer")
    ↓
Chainlit UI 层
    ├─ Step 组件展示思考内容 (可折叠)
    └─ Message 组件展示答案
```

### 关键组件变更

| 组件 | 变更内容 | 影响范围 |
|------|---------|---------|
| `ModelConfig` | 添加 `model_variant` 字段 | 配置层 |
| `DeepSeekWrapper` | 解析 `reasoning_content` | 模型层 |
| `StreamChunk` | 添加 `chunk_type` 字段 | 数据模型 |
| `app.py` | UI 集成，模型选择控件 | 应用层 |

## 📝 规范变更 (Deltas)

### ADDED 要求 (3个)

1. **DeepSeek 模型选择** (4 scenarios)
   - 选择 deepseek-chat 模型
   - 选择 deepseek-reasoner 模型
   - 默认模型配置
   - 模型切换

2. **思考内容展示** (4 scenarios)
   - 流式展示思考过程
   - 自动折叠思考内容
   - 手动展开思考内容
   - 无思考内容的情况

3. **响应解析和处理** (3 scenarios)
   - 解析包含思考内容的响应
   - 解析不包含思考内容的响应
   - 处理格式异常

### MODIFIED 要求 (2个)

1. **模型配置** - 扩展支持 model_variant 参数
2. **Chainlit界面集成** - 添加模型选择和思考展示功能

## 🎯 实现任务

### 总计 6 个阶段，23 个任务

1. **配置层扩展** (3 tasks)
2. **模型包装器更新** (4 tasks)
3. **UI 集成** (5 tasks)
4. **命令系统扩展** (3 tasks)
5. **文档更新** (3 tasks)
6. **测试验证** (5 tasks)

详见：[tasks.md](./tasks.md)

## 🎨 UI 效果预览

### 使用 deepseek-reasoner 时

```
┌─────────────────────────────────────┐
│ 💭 思考中...               [展开 ▼] │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 首先，我需要分析这个问题...         │
│ 让我们考虑以下几个方面...           │
│ 综合以上分析...                     │
└─────────────────────────────────────┘
                ↓
        [用户开始看到答案]
                ↓
┌─────────────────────────────────────┐
│ 💡 思考过程                [折叠 ▶] │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 💬 Assistant                         │
│                                     │
│ 根据以上分析，答案是...             │
│ ...                                 │
└─────────────────────────────────────┘
```

### 使用 deepseek-chat 时

```
┌─────────────────────────────────────┐
│ 💬 Assistant                         │
│                                     │
│ 答案是...                           │
│ ...                                 │
└─────────────────────────────────────┘
```

## 🔒 兼容性保证

✅ **向后兼容**:
- 现有 deepseek-chat 用户不受影响
- 默认行为保持不变
- 可选择性启用新功能

✅ **非破坏性**:
- 不影响其他模型提供商（OpenAI, Anthropic）
- 不改变现有 API 接口
- 配置可回滚

## 📚 文档结构

```
add-deepseek-reasoner-support/
├── README.md                    ← 功能总览
├── PROPOSAL_SUMMARY.md          ← 本文档
├── proposal.md                  ← 正式提案
├── tasks.md                     ← 实现任务
├── design.md                    ← 技术设计
└── specs/
    └── model-invocation/
        └── spec.md              ← 规范变更 (delta)
```

## 🚀 下一步

1. **审核批准**: 提交提案供团队审核
2. **实现开发**: 按照 tasks.md 顺序实现
3. **测试验证**: 确保所有场景正常工作
4. **文档更新**: 更新用户文档和 README
5. **归档**: 完成后归档到 `changes/archive/`

## 📞 联系方式

如有疑问或建议，请查看：
- [design.md](./design.md) - 技术决策和风险分析
- [tasks.md](./tasks.md) - 详细实现步骤
- [model-invocation spec](../../specs/model-invocation/spec.md) - 现有规范

---

**验证命令**:
```bash
openspec validate add-deepseek-reasoner-support --strict
```

**查看详情**:
```bash
openspec show add-deepseek-reasoner-support
```

