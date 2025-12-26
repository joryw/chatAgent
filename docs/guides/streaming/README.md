# 流式输出功能

## 概述

本项目实现了**流式输出（Streaming）**功能，使 AI 响应能够像打字一样逐字显示，提供更好的用户体验。

## 功能特性

### ✨ 核心特性

1. **实时响应显示**
   - 响应内容逐字逐句实时显示
   - 无需等待完整响应生成
   - 提供即时反馈体验

2. **多提供商支持**
   - ✅ OpenAI (GPT-4, GPT-3.5)
   - ✅ DeepSeek
   - ✅ Anthropic (Claude)

3. **错误处理**
   - 流式传输中断自动处理
   - 带重试机制（最多 3 次）
   - 用户友好的错误消息

4. **性能优化**
   - 异步处理，不阻塞 UI
   - 最小延迟
   - 高效的 token 计数

## 技术实现

### 架构设计

```
用户输入
    ↓
app.py (Chainlit UI)
    ↓
BaseModelWrapper.generate_stream()
    ↓
├─ OpenAIWrapper
├─ DeepSeekWrapper
└─ AnthropicWrapper
    ↓
API 流式响应
    ↓
逐块更新 UI
```

### 代码示例

#### 1. 基础接口 (`src/models/base.py`)

```python
@dataclass
class StreamChunk:
    """流式响应的单个块"""
    content: str
    finish_reason: Optional[str] = None

class BaseModelWrapper(ABC):
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """生成流式响应"""
        pass
```

#### 2. OpenAI 实现 (`src/models/openai_wrapper.py`)

```python
async def generate_stream(
    self,
    prompt: str,
    system_message: Optional[str] = None,
    **kwargs
) -> AsyncIterator[StreamChunk]:
    """OpenAI 流式响应"""
    
    # 准备消息
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})
    
    # 调用流式 API
    stream = self.client.chat.completions.create(
        model=self.config.model_name,
        messages=messages,
        stream=True,  # 启用流式
    )
    
    # 逐块产出响应
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield StreamChunk(
                content=chunk.choices[0].delta.content,
                finish_reason=chunk.choices[0].finish_reason,
            )
```

#### 3. Chainlit 集成 (`app.py`)

```python
# 创建消息
response_msg = cl.Message(content="", author="Assistant")
await response_msg.send()

# 流式生成
full_response = ""
async for chunk in model_wrapper.generate_stream(
    prompt=user_message,
    system_message=DEFAULT_SYSTEM_MESSAGE,
):
    full_response += chunk.content
    response_msg.content = full_response
    await response_msg.update()  # 实时更新 UI
```

## 使用指南

### 启动应用

```bash
# 使用脚本启动
./run.sh

# 或直接使用 chainlit
chainlit run app.py -w
```

### 体验流式输出

1. **打开浏览器**: 访问 `http://localhost:8000`
2. **选择提供商**: 系统会自动使用配置的默认提供商
3. **开始对话**: 输入消息，观察响应逐字显示
4. **切换提供商**: 使用 `/switch <provider>` 命令

### 示例对话

```
You: 请详细解释什么是流式输出？