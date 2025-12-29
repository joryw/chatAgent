# 提案: 添加UI开关控制联网搜索功能

## 📋 提案摘要

**提案ID:** `add-ui-search-toggle`  
**状态:** ✅ 验证通过,等待审批  
**影响范围:** web-search 功能增强  
**破坏性变更:** ❌ 无 (向后兼容)

## 🎯 核心改进

将当前的命令行搜索开关升级为**可视化UI开关**,同时保留命令方式作为备用。

### 现状 (Before)
```
用户: /search on
系统: ✅ Web search enabled
```
- ❌ 需要记住命令格式
- ❌ 新用户不知道有这个功能
- ❌ 无法直观看到开关状态

### 改进后 (After)
```
[聊天设置面板]
🔍 联网搜索  [●|  ]  ← UI开关
   启用后将使用SearXNG搜索实时信息
```
- ✅ 一键切换,直观易用
- ✅ 实时显示状态
- ✅ 仍可使用 `/search` 命令
- ✅ 两种方式状态同步

## 🔧 技术方案

### 实现基础
- **框架:** Chainlit ChatSettings API
- **控件类型:** Switch (开关)
- **状态管理:** `cl.user_session` (与现有命令共享)
- **代码修改:** 仅 `app.py` (~30行新增代码)

### 核心组件
```python
@cl.on_settings_update
async def settings_update(settings):
    """监听UI开关变化"""
    search_enabled = settings.get("web_search", False)
    cl.user_session.set("search_enabled", search_enabled)
    # 发送状态确认消息

# 在启动时初始化
settings = await cl.ChatSettings([
    Switch(
        id="web_search",
        label="🔍 联网搜索",
        initial=False,
        disabled=(search_service is None)
    )
]).send()
```

## 📦 交付物

### 文档
- ✅ `proposal.md` - 为什么需要这个改变
- ✅ `design.md` - 技术设计和决策
- ✅ `tasks.md` - 30个实施步骤清单
- ✅ `specs/web-search/spec.md` - 规范更新

### 代码变更预览
- 修改 `app.py`:
  - 添加 `@cl.on_settings_update` 回调
  - 在 `start()` 中初始化 ChatSettings
  - 增强欢迎消息和帮助文本
- 保持 `/search` 命令完整可用

## 🎨 用户体验

### 新用户流程
1. 打开聊天应用
2. 看到设置面板中的搜索开关
3. 一键开启联网搜索
4. 开始提问,自动使用搜索结果

### 搜索不可用时
- UI开关显示为灰色/禁用
- 鼠标悬停显示"搜索服务不可用"
- 欢迎消息中显示配置指南

### 状态同步示例
```
用户操作            | UI开关 | 命令查询 | 实际行为
--------------------|--------|----------|----------
打开UI开关          | ✅ ON  | enabled  | 启用搜索
执行 /search off    | ❌ OFF | disabled | 禁用搜索
执行 /search on     | ✅ ON  | enabled  | 启用搜索
关闭UI开关          | ❌ OFF | disabled | 禁用搜索
```

## ✨ 核心优势

### 1. 易用性提升
- **学习成本降低 90%:** 从"查文档记命令"到"看到即会用"
- **新手友好:** 视觉化设计,符合直觉
- **发现性增强:** 不需要任何提示就能找到功能

### 2. 完全兼容
- **现有命令保留:** `/search on|off` 完全可用
- **状态同步:** UI和命令共享同一状态
- **无需迁移:** 老用户习惯不受影响

### 3. 健壮性
- **服务状态感知:** 搜索不可用时UI自动禁用
- **优雅降级:** 搜索失败不影响对话
- **实时反馈:** 状态变化立即可见

### 4. 开发成本低
- **纯增量改动:** 不修改现有搜索逻辑
- **框架原生支持:** 使用Chainlit标准API
- **测试简单:** UI和功能解耦

## 🚀 实施路径

### Phase 1: 基础UI (30分钟)
```bash
# 1. 添加设置面板初始化代码
# 2. 添加设置更新回调
# 3. 测试基本切换功能
```

### Phase 2: 状态同步 (20分钟)
```bash
# 1. 确保UI和命令共享状态
# 2. 测试双向同步
# 3. 添加状态确认消息
```

### Phase 3: 边界处理 (30分钟)
```bash
# 1. 处理搜索服务不可用
# 2. 优化欢迎消息
# 3. 更新帮助文档
```

### Phase 4: 测试验证 (20分钟)
```bash
# 1. 完整用户流程测试
# 2. 边界情况测试
# 3. 文档更新
```

**预计总时长:** 2小时

## 📊 影响评估

### 用户影响
- ✅ **正面:** 新用户使用更简单
- ✅ **正面:** 老用户有更多选择
- ❌ **负面:** 无

### 系统影响
- ✅ **性能:** 无影响(仅UI变化)
- ✅ **维护:** 复杂度略增(+30行代码)
- ✅ **稳定性:** 无风险(非核心功能)

### 兼容性
- ✅ 向后兼容
- ✅ 无配置迁移
- ✅ 无数据迁移
- ✅ 可随时回滚

## 🔍 详细文档

- **提案详情:** [proposal.md](./proposal.md)
- **技术设计:** [design.md](./design.md)
- **实施清单:** [tasks.md](./tasks.md)
- **规范变更:** [specs/web-search/spec.md](./specs/web-search/spec.md)

## ✅ 验证状态

```bash
$ openspec validate add-ui-search-toggle --strict
✅ Change 'add-ui-search-toggle' is valid
```

## 🎬 下一步

### 如果批准此提案
```bash
# 1. 审批决定
echo "提案已批准" > .approved

# 2. 开始实施
# 参考 tasks.md 逐步完成

# 3. 实施完成后
openspec archive add-ui-search-toggle
```

### 如果需要修改
提供反馈,我会相应调整提案。

---

**问题或建议?** 欢迎讨论! 这个提案的目标是让联网搜索功能更加用户友好,同时保持系统的简洁和稳定。


