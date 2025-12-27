# 设计文档: UI搜索开关

## Context
当前系统使用斜杠命令 `/search on|off` 控制联网搜索功能。这种方式虽然功能完整,但对于不熟悉命令行的用户来说存在使用障碍。

**现状分析:**
- ✅ 命令方式灵活,适合高级用户
- ❌ 新用户可能不知道有搜索功能
- ❌ 需要查看帮助文档才能了解命令
- ❌ 无法直观看到当前开关状态

**技术约束:**
- 必须使用 Chainlit 框架提供的UI组件
- 不能引入新的依赖
- 需要保持现有功能的完整性

**用户群体:**
- 技术用户: 习惯命令行,可能更喜欢命令方式
- 普通用户: 需要可视化界面,希望简单易用

## Goals / Non-Goals

**Goals:**
1. 提供直观的UI开关控制搜索功能
2. 保持现有命令方式的完整性(向后兼容)
3. 两种控制方式能够互相同步状态
4. 搜索服务不可用时,UI开关显示为禁用状态

**Non-Goals:**
- 不改变搜索功能本身的实现
- 不添加更多的配置选项(如搜索引擎选择)
- 不改变搜索结果的展示方式
- 不修改环境变量配置方式

## Decisions

### Decision 1: 使用 Chainlit ChatSettings
**选择:** 使用 Chainlit 的 `ChatSettings` API 创建设置面板

**原因:**
- Chainlit 原生支持,无需额外依赖
- 提供标准的Switch控件,符合用户习惯
- 与聊天界面自然集成
- 支持实时更新和状态同步

**替代方案:**
1. **自定义UI组件:** 需要前端开发,复杂度高
2. **使用 Actions API:** 适合单次操作,不适合状态切换
3. **在欢迎消息中嵌入按钮:** 状态不持久,用户体验差

### Decision 2: 保留命令方式作为备用
**选择:** 保持 `/search on|off` 命令完整可用

**原因:**
- 向后兼容性: 不影响现有用户习惯
- 灵活性: 高级用户可能更喜欢命令方式
- 可脚本化: 便于自动化测试和演示
- 降低风险: UI问题不会完全阻碍功能使用

**实现:** 
- 命令和UI共享同一个session状态 (`search_enabled`)
- 任一方式修改状态,另一方都能反映

### Decision 3: 默认状态为关闭
**选择:** 搜索开关默认为关闭状态

**原因:**
- 与现有行为一致(第105行 `search_enabled=False`)
- 避免不必要的搜索请求和延迟
- 让用户主动选择何时需要联网信息
- 节省搜索服务资源

### Decision 4: 搜索不可用时禁用UI开关
**选择:** 当 `search_service` 为 None 时,UI开关显示为禁用状态

**原因:**
- 避免用户困惑(开关打开但搜索不工作)
- 清晰传达搜索功能的可用性
- 引导用户查看配置指南

**UI行为:**
- 开关显示为灰色/禁用状态
- 鼠标悬停时显示"搜索服务不可用"提示
- 在欢迎消息中显示配置指南链接

## Technical Implementation

### 组件结构

```python
# 在 app.py 中添加

from chainlit.input_widget import Switch

@cl.on_settings_update
async def settings_update(settings):
    """处理设置更新"""
    search_enabled = settings.get("web_search", False)
    search_service = cl.user_session.get("search_service")
    
    if search_service:
        cl.user_session.set("search_enabled", search_enabled)
        status = "✅ 已启用" if search_enabled else "❌ 已禁用"
        await cl.Message(
            content=f"联网搜索{status}",
            author="System"
        ).send()
    else:
        await cl.Message(
            content="⚠️ 搜索服务不可用,无法启用",
            author="System"
        ).send()

# 在 start() 函数中初始化设置
search_service = cl.user_session.get("search_service")
settings = await cl.ChatSettings(
    [
        Switch(
            id="web_search",
            label="🔍 联网搜索",
            initial=False,
            description="启用后将使用SearXNG搜索实时信息",
            disabled=(search_service is None),
        )
    ]
).send()
```

### 状态管理

**状态存储位置:** `cl.user_session.set("search_enabled", bool)`

**状态修改来源:**
1. UI开关: 通过 `@cl.on_settings_update` 回调
2. `/search` 命令: 在 `handle_command` 函数中

**状态读取位置:**
1. `main()` 函数: 决定是否执行搜索
2. `/config` 命令: 显示当前状态
3. `/search` 命令: 显示当前状态

**状态同步机制:**
- UI和命令共享同一个 `user_session` 键
- 修改时立即生效,无需刷新
- ChatSettings 对象在会话期间保持

### 用户流程

```
用户启动聊天
    ↓
系统初始化 (on_chat_start)
    ↓
检查搜索服务可用性
    ↓
    ├─ 可用: 创建启用的搜索开关
    └─ 不可用: 创建禁用的搜索开关 + 显示配置提示
    ↓
用户看到欢迎消息(包含搜索状态和开关位置说明)
    ↓
用户发送消息
    ↓
    ├─ 开关开启 → 执行搜索 → 使用搜索结果生成回答
    └─ 开关关闭 → 直接使用模型生成回答
```

## Risks / Trade-offs

### Risk 1: UI性能
**风险:** 频繁切换开关可能导致多次状态更新消息

**缓解措施:**
- 消息简短,减少UI渲染负担
- 不在切换时执行任何耗时操作
- 状态更新是异步的,不阻塞主流程

**监控:** 测试快速切换10次的响应时间

### Risk 2: 状态不同步
**风险:** UI开关状态与实际会话状态可能不一致

**缓解措施:**
- 使用单一数据源 (`user_session`)
- 任何修改都通过同一个session键
- 在 `/config` 命令中显示权威状态

**测试:** 
1. UI开启 → 命令查询 → 验证一致
2. 命令开启 → UI状态 → 验证一致
3. 会话重启 → 验证状态重置

### Risk 3: 搜索服务状态变化
**风险:** 搜索服务可能在会话中途变为不可用

**当前行为:** 
- 搜索失败时优雅降级
- 显示错误消息但不中断对话

**UI影响:**
- 开关仍然可操作
- 但搜索会失败并降级
- 用户会看到搜索失败提示

**改进空间(Future):**
- 可以添加定期健康检查
- 动态更新UI开关的可用状态
- 不在本次改动范围内

## Migration Plan

**部署步骤:**
1. 更新代码到生产环境
2. 重启 Chainlit 应用
3. 新会话自动获得UI开关功能
4. 现有会话在下次重启后生效

**回滚计划:**
- 恢复到之前的 `app.py` 版本
- 只影响UI部分,搜索功能本身不变
- 命令方式始终可用作为后备

**用户通知:**
- 不需要特别通知
- 用户打开应用时自然发现新功能
- 可以在更新日志中提及

**数据迁移:**
- 不需要数据迁移
- 状态存储在会话级别,不持久化
- 每次会话都是全新初始化

## Open Questions

1. **是否需要添加搜索开关的快捷键?**
   - 例如: Ctrl+S 切换搜索
   - 决策: 暂不实现,避免快捷键冲突,可以在后续版本考虑

2. **是否在搜索开关旁边显示搜索服务状态指示器?**
   - 例如: 🟢 SearXNG 正常 / 🔴 SearXNG 不可用
   - 决策: 当前在欢迎消息中已有状态显示,UI开关通过禁用状态体现,暂不额外添加

3. **是否需要记住用户的搜索偏好(跨会话)?**
   - 例如: 使用浏览器 localStorage 或数据库
   - 决策: 暂不实现,保持会话级别状态更简单,避免隐私问题

4. **搜索开关是否应该影响搜索历史的显示?**
   - 决策: 不影响,历史消息的搜索结果仍然正常显示


