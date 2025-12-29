# 快速参考卡片 🚀

## 提案信息

- **Change ID**: `add-deepseek-reasoner-support`
- **状态**: 待审核 (0/23 tasks)
- **影响范围**: model-invocation spec
- **总行数**: 635 行文档

## 核心特性

```
🎯 模型选择 (参照联网搜索实现)
   ├─ deepseek-chat (标准对话)
   └─ deepseek-reasoner (推理模型)

💭 思考展示
   ├─ 流式输出思考过程
   ├─ 自动折叠 (开始回答时)
   └─ 手动展开/折叠

🔧 配置方式
   ├─ UI 设置面板 (推荐) - Select 下拉菜单
   │  └─ 只在 DeepSeek 提供商下显示
   ├─ 环境变量: DEEPSEEK_MODEL_VARIANT (默认值)
   └─ /config 命令查看当前设置
```

## 关键文件

| 文件 | 大小 | 用途 |
|------|------|------|
| proposal.md | 33 行 | 为什么、改什么 |
| tasks.md | 37 行 | 23 个实现任务 |
| design.md | 160 行 | 技术决策、风险 |
| spec.md | 123 行 | 规范变更 (5 deltas) |
| README.md | 100 行 | 功能总览 |
| PROPOSAL_SUMMARY.md | 182 行 | 完整总结 |

## 变更统计

```
📊 规范变更
├─ ADDED: 3 个新需求 (11 scenarios)
└─ MODIFIED: 2 个现有需求

🔨 实现任务
├─ 配置层: 3 tasks
├─ 模型层: 4 tasks
├─ UI 层: 5 tasks
├─ 命令系统: 3 tasks
├─ 文档: 3 tasks
└─ 测试: 5 tasks
```

## 使用示例

### 场景 1: 复杂推理
```
步骤 1: 打开设置面板
  - 点击右上角 ⚙️ 图标

步骤 2: 选择推理模型
  - 在 "🤖 DeepSeek 模型" 下拉菜单中
  - 选择 "deepseek-reasoner"

步骤 3: 提问
  "如果把地球缩小到篮球大小，珠穆朗玛峰有多高？"

步骤 4: 观察思考过程
  💭 思考中...
     ├─ 计算地球半径...
     ├─ 计算缩放比例...
     └─ 计算珠峰高度...
  
  💬 答案: 大约 0.7 毫米...
```

### 场景 2: 快速对话
```
步骤 1: 在设置面板选择 "deepseek-chat"

步骤 2: 提问
  "今天星期几？"

步骤 3: 直接回答（无思考过程）
  💬 今天是星期五
```

## 命令速查

```bash
# 查看提案
openspec show add-deepseek-reasoner-support

# 验证提案
openspec validate add-deepseek-reasoner-support --strict

# 查看任务列表
cat openspec/changes/add-deepseek-reasoner-support/tasks.md

# 查看设计文档
cat openspec/changes/add-deepseek-reasoner-support/design.md
```

## 实现检查清单

- [ ] 配置层：添加 model_variant 支持
- [ ] 模型层：解析 reasoning_content
- [ ] UI 层：实现思考内容展示
- [ ] 命令：扩展 /switch 命令
- [ ] 文档：更新 README 和指南
- [ ] 测试：验证所有场景

## 关键技术点

1. **UI 一致性**: 参照联网搜索，使用 `Select` 控件
2. **响应解析**: 识别 `reasoning_content` 字段
3. **流式处理**: 使用 `StreamChunk` 区分思考和答案
4. **折叠组件**: 使用 Chainlit `Step` 实现自动折叠
5. **条件显示**: 只在 DeepSeek 下显示模型选择器
6. **配置层级**: 环境变量 → UI 选择 → 会话状态
7. **向后兼容**: 保持 deepseek-chat 行为不变

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| API 格式变化 | 防御性解析 + 降级处理 |
| 流式响应复杂 | 状态机管理 |
| UI 性能 | 批量更新 (100ms) |

## 审批流程

1. ✅ 提案创建
2. ⏳ 团队审核
3. ⏳ 实现开发
4. ⏳ 测试验证
5. ⏳ 文档更新
6. ⏳ 归档发布

## 需要的批准

- [ ] 技术架构审核
- [ ] UI/UX 设计确认
- [ ] 安全性评估
- [ ] 性能测试计划

---

**创建日期**: 2025-12-27  
**OpenSpec 版本**: 符合最新规范  
**验证状态**: ✅ Strict mode passed

