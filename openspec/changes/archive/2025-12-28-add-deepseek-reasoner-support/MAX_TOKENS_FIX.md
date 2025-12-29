# DeepSeek max_tokens 限制修复

## 问题描述

用户报告了以下错误：
```
Error code: 400 - {'error': {'message': 'Invalid max_tokens value, the valid range of max_tokens is [1, 8192]', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
```

## 问题根源

用户对 DeepSeek API 的两个重要概念产生了混淆：

### 1. 上下文长度（Context Length）
- **值**: 128K（两个模型相同）
- **含义**: 模型能够**读取和理解**的输入文本的最大长度
- **包括**: 用户提问、历史对话、系统提示词等

### 2. 输出长度（max_tokens）
- **deepseek-chat**: 
  - 默认 4K
  - 最大 **8K** (8192)
- **deepseek-reasoner**:
  - 默认 32K
  - 最大 **64K** (65536)
- **含义**: 模型**生成回复**的最大长度

## 解决方案

### 1. 配置验证（`src/config/model_config.py`）

添加了基于模型变体的 `max_tokens` 验证和自动调整：

```python
# DeepSeek API max_tokens valid range depends on model variant:
# - deepseek-chat: [1, 8192] (8K max)
# - deepseek-reasoner: [1, 65536] (64K max)
max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000"))

if model_variant == "deepseek-reasoner":
    # deepseek-reasoner supports up to 64K output
    max_limit = 65536
else:
    # deepseek-chat supports up to 8K output
    max_limit = 8192

if max_tokens > max_limit:
    max_tokens = max_limit
elif max_tokens < 1:
    max_tokens = 1
```

### 2. UI 模型切换处理（`app.py`）

在用户通过 UI 切换模型时，自动调整 `max_tokens`：

```python
# Update max_tokens based on model variant
# deepseek-chat: max 8K, deepseek-reasoner: max 64K
if deepseek_model == "deepseek-reasoner":
    # Ensure max_tokens is within reasoner's limit (64K)
    if model_wrapper.config.max_tokens > 65536:
        model_wrapper.config.max_tokens = 65536
else:
    # Ensure max_tokens is within chat's limit (8K)
    if model_wrapper.config.max_tokens > 8192:
        model_wrapper.config.max_tokens = 8192
```

### 3. 文档更新

#### `env.example`
添加了清晰的 `max_tokens` 说明：
```bash
# max_tokens (output length) valid range:
# - deepseek-chat: [1, 8192] (8K max)
# - deepseek-reasoner: [1, 65536] (64K max)
# Note: Context length (input) is 128K for both models
DEEPSEEK_MAX_TOKENS=2000
```

#### `README.md`
添加了技术规格对比表：

| Specification | deepseek-chat | deepseek-reasoner |
|--------------|---------------|-------------------|
| **Context Length** (Input) | 128K | 128K |
| **Output Length** (max_tokens) | Default 4K, Max **8K** | Default 32K, Max **64K** |
| **Reasoning Display** | ❌ | ✅ |

#### `docs/guides/quick-start/README.md`
在配置示例中添加了说明：
```bash
DEEPSEEK_MAX_TOKENS=2000  # Max output: 8K (chat) / 64K (reasoner). Context: 128K
```

## 影响范围

### 修改的文件
1. `src/config/model_config.py` - 配置加载和验证
2. `app.py` - UI 模型切换处理
3. `env.example` - 配置示例
4. `README.md` - 主文档
5. `docs/guides/quick-start/README.md` - 快速开始文档

### 兼容性
- ✅ 向后兼容：现有配置不受影响
- ✅ 自动修正：超出范围的值会自动调整到有效范围
- ✅ 无需手动干预：用户不需要修改现有的 `.env` 文件

## 测试验证

### 场景 1: deepseek-chat 模型
- 配置 `DEEPSEEK_MAX_TOKENS=2000` ✅
- 配置 `DEEPSEEK_MAX_TOKENS=8192` ✅
- 配置 `DEEPSEEK_MAX_TOKENS=10000` → 自动调整为 8192 ✅

### 场景 2: deepseek-reasoner 模型
- 配置 `DEEPSEEK_MAX_TOKENS=2000` ✅
- 配置 `DEEPSEEK_MAX_TOKENS=65536` ✅
- 配置 `DEEPSEEK_MAX_TOKENS=100000` → 自动调整为 65536 ✅

### 场景 3: UI 模型切换
- deepseek-chat → deepseek-reasoner: max_tokens 保持不变（如果 ≤ 8192）✅
- deepseek-reasoner → deepseek-chat: max_tokens 自动调整（如果 > 8192）✅

## 用户指引

### 推荐配置
```bash
# 保守配置（适合大多数场景）
DEEPSEEK_MAX_TOKENS=2000

# 中等配置（平衡成本和输出长度）
DEEPSEEK_MAX_TOKENS=4000

# 最大配置（需要长输出时）
# deepseek-chat: 最大 8192
# deepseek-reasoner: 最大 65536
```

### 注意事项
1. **成本考虑**: 输出长度直接影响 API 调用成本
2. **模型差异**: 
   - `deepseek-chat` 最适合短到中等长度的对话
   - `deepseek-reasoner` 适合需要详细推理和长输出的场景
3. **自动调整**: 系统会自动确保 `max_tokens` 在有效范围内，无需担心设置错误

## 状态

✅ **已完成** - 2025-12-27

所有修改已实现并测试通过，文档已更新。

