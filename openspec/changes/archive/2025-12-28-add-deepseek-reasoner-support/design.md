# 设计文档：DeepSeek Reasoner 支持

## Context

DeepSeek 提供了两种主要模型：
1. **deepseek-chat**: 标准对话模型，直接生成答案
2. **deepseek-reasoner**: 推理模型，先进行思考推理，再给出答案

reasoner 模型的 API 响应包含两部分：
- `reasoning_content`: 模型的思考过程（推理步骤）
- `content`: 最终答案

当前系统只支持 deepseek-chat，需要扩展以支持 reasoner 模型，并提供良好的用户体验来展示思考过程。

## Goals / Non-Goals

**Goals:**
- 支持用户在 deepseek-chat 和 deepseek-reasoner 之间选择
- 流式展示 reasoner 模型的思考过程
- 当开始输出答案时自动折叠思考内容
- 保持向后兼容，不影响现有 deepseek-chat 用户

**Non-Goals:**
- 不修改其他提供商（OpenAI, Anthropic）的行为
- 不实现思考内容的后续编辑或交互功能
- 不保存思考内容到对话历史（只保存最终答案）

## Decisions

### Decision 1: 模型选择方式

**选择**: 通过 Chainlit 设置面板的下拉菜单（Select 控件）选择模型，与联网搜索的 UI 实现方式保持一致。

**理由**:
- 与现有的联网搜索 UI 控件保持一致的用户体验
- 使用 `Select` 控件适合多选项场景（deepseek-chat / deepseek-reasoner）
- 易于发现和使用，直接在设置面板中可见
- 只在使用 DeepSeek 提供商时显示，避免混淆
- 实时生效，无需重启应用

**实现参照**: 
```python
from chainlit.input_widget import Select

chat_settings = cl.ChatSettings([
    Select(
        id="deepseek_model",
        label="🤖 DeepSeek 模型",
        values=["deepseek-chat", "deepseek-reasoner"],
        initial_value="deepseek-chat",
        description="选择 DeepSeek 模型类型"
    )
])
```

**替代方案**:
- 使用 /switch 命令：不如 UI 直观，但保留作为提供商切换使用
- 自动检测：可能导致意外切换，用户体验不可控

### Decision 2: 思考内容展示方式

**选择**: 使用 Chainlit 的可折叠消息块（Step）来展示思考内容。

**理由**:
- Chainlit 原生支持 Step 组件，可以折叠/展开
- 视觉上与正式回答有明确区分
- 支持流式更新内容
- 与项目现有的 UI 组件风格一致

**实现细节**:
```python
# 在 app.py 的消息处理中
async with cl.Step(name="💭 思考中...", type="tool") as thinking_step:
    # 流式更新思考内容
    reasoning_content = ""
    async for chunk in model_wrapper.generate_stream(...):
        if chunk.chunk_type == "reasoning":
            reasoning_content += chunk.content
            thinking_step.output = reasoning_content
            await thinking_step.update()
        elif chunk.chunk_type == "answer":
            # 切换到答案阶段，折叠思考内容
            thinking_step.name = "💡 思考过程"
            thinking_step.collapsed = True
            await thinking_step.update()
            
            # 开始显示正式回答
            response_msg = cl.Message(content="", author="Assistant")
            await response_msg.send()
            # 继续流式更新答案...
```

**替代方案**:
- 使用单独的消息：无法折叠，会占用过多空间
- 使用 markdown 折叠：Chainlit 不完全支持，渲染效果差

### Decision 3: 响应解析策略

**选择**: 在 DeepSeekWrapper 中解析 API 响应，返回带标记的 StreamChunk。

**理由**:
- 保持关注点分离：包装器负责 API 通信和解析
- UI 层只需处理不同类型的 chunk
- 便于单元测试

**StreamChunk 扩展**:
```python
@dataclass
class StreamChunk:
    content: str
    chunk_type: str = "answer"  # "reasoning" or "answer"
    finish_reason: Optional[str] = None
```

### Decision 4: 配置管理

**选择**: 在现有的 DeepSeek 配置中添加 model_variant 字段，同时支持 UI 运行时切换。

**配置层级**:
1. **环境变量** (默认值):
```python
# .env
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_MODEL_VARIANT=deepseek-chat  # 默认模型
```

2. **UI 设置面板** (运行时):
- 用户可在设置面板中选择模型
- 选择会保存到 user_session
- 优先级高于环境变量

3. **会话状态** (当前值):
```python
cl.user_session.set("deepseek_model_variant", "deepseek-reasoner")
```

**理由**:
- 保持配置简单，只需一个新字段
- 不破坏现有配置（默认为 deepseek-chat）
- 支持运行时动态切换（通过 UI）
- 与联网搜索的配置方式保持一致

## Risks / Trade-offs

### Risk 1: API 响应格式变化
- **风险**: DeepSeek 可能更改 reasoning_content 字段的格式或位置
- **缓解**: 添加防御性解析代码，处理字段缺失的情况

### Risk 2: 流式响应的复杂性
- **风险**: 思考内容和答案可能同时流式返回，需要正确区分和展示
- **缓解**: 使用明确的状态机管理流式响应的不同阶段

### Risk 3: UI 性能
- **风险**: 思考内容可能很长，频繁更新可能影响性能
- **缓解**: 
  - 批量更新（每 100ms 更新一次）
  - 使用 Chainlit 的优化更新机制

### Trade-off 1: 对话历史
- **决策**: 只保存最终答案到对话历史，不保存思考内容
- **原因**: 思考内容可能很长，会快速消耗 token 限制
- **影响**: 用户无法在后续对话中引用思考过程

## Migration Plan

### 阶段 1: 配置和模型层（非破坏性）
1. 添加新配置选项（默认值保持兼容）
2. 更新 DeepSeekWrapper（向后兼容）
3. 部署到测试环境验证

### 阶段 2: UI 集成
1. 添加模型选择控件
2. 实现思考内容展示
3. 更新命令系统

### 阶段 3: 文档和发布
1. 更新用户文档
2. 添加使用示例
3. 发布更新公告

### 回滚计划
- 如果出现问题，可以通过环境变量禁用 reasoner 模型
- 保持 deepseek-chat 作为默认选项
- 不影响其他提供商的功能

## Open Questions

1. **Q**: 是否需要限制思考内容的长度？
   - **A**: 暂不限制，依赖 API 的默认行为。如果发现性能问题再添加限制。

2. **Q**: 是否支持其他提供商的 reasoning 模式？
   - **A**: 不在本次变更范围内。OpenAI 和 Anthropic 的 reasoning 模式可以作为未来的独立功能添加。

3. **Q**: 思考内容是否需要支持用户交互（如暂停、跳过）？
   - **A**: 不在本次范围内。先实现基础的展示功能，根据用户反馈决定是否添加交互功能。

