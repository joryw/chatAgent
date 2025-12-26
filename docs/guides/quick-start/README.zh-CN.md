---
title: 快速开始指南
title_en: Quick Start Guide
type: guide
audience: [users, developers]
created: 2024-12-26
updated: 2024-12-26
version: 1.0.0
tags: [quickstart, setup, tutorial]
lang: zh-CN
status: published
related:
  - ../../guides/configuration/README.md
  - ../../development/contributing/guide.md
---

# 快速开始指南

> **预计时间**: 5-10 分钟  
> **难度**: 初级

本指南将帮助你在几分钟内启动并运行 AI Agent 项目。

## 📋 前置条件

在开始之前，请确保你已经安装：

- **Python 3.11 或更高版本**
  ```bash
  python --version  # 应该显示 3.11.x 或更高
  ```

- **至少一个 LLM 提供商的 API 密钥**:
  - OpenAI API Key (推荐)
  - Anthropic API Key
  - DeepSeek API Key

## 🚀 安装步骤

### 1. 克隆仓库

```bash
git clone <repository-url>
cd chatAgent
```

### 2. 创建虚拟环境

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

这将安装所有必需的 Python 包，包括：
- LangChain
- Chainlit
- OpenAI SDK
- Anthropic SDK
- 其他依赖

### 4. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
cp env.example .env
```

编辑 `.env` 文件，添加你的 API 密钥：

```bash
# OpenAI 配置（推荐）
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# DeepSeek 配置（可选）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Anthropic 配置（可选）
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# 默认提供商
DEFAULT_PROVIDER=openai

# 日志级别
LOG_LEVEL=INFO
```

⚠️ **重要**: 
- 将 `sk-your-xxx-api-key-here` 替换为你的真实 API 密钥
- 不要将 `.env` 文件提交到 Git（已在 .gitignore 中）

### 5. 启动应用

```bash
chainlit run app.py -w
```

参数说明：
- `-w`: 启用监视模式，代码更改时自动重新加载

### 6. 访问界面

打开浏览器访问：

```
http://localhost:8000
```

🎉 **恭喜！** 你现在可以开始与 AI Agent 对话了！

## 💬 基本使用

### 发送消息

在聊天界面中输入你的消息并按 Enter 键。AI 将使用配置的模型进行响应。

**示例对话**:
```
你: 你好，请介绍一下自己
AI: 你好！我是一个 AI 助手...
```

### 斜杠命令

应用支持以下命令：

| 命令 | 说明 | 示例 |
|------|------|------|
| `/help` | 显示可用命令 | `/help` |
| `/config` | 查看当前模型配置 | `/config` |
| `/switch <provider>` | 切换模型提供商 | `/switch deepseek` |
| `/reset` | 清除对话历史 | `/reset` |

### 切换模型提供商

在对话过程中切换不同的 LLM 提供商：

```
/switch openai      # 切换到 OpenAI GPT-4
/switch deepseek    # 切换到 DeepSeek
/switch anthropic   # 切换到 Anthropic Claude
```

## 🔧 配置选项

### 模型参数

你可以通过环境变量调整模型参数：

| 参数 | 范围 | 说明 | 默认值 |
|------|------|------|--------|
| `TEMPERATURE` | 0.0-2.0 | 控制随机性。越高越有创意 | 0.7 |
| `MAX_TOKENS` | 正整数 | 生成的最大令牌数 | 2000 |
| `TOP_P` | 0.0-1.0 | 核采样参数 | 1.0 |
| `TIMEOUT` | 秒 | API 请求超时时间 | 30 |

### 示例配置

**更有创意的回答**:
```bash
OPENAI_TEMPERATURE=1.2
OPENAI_MAX_TOKENS=3000
```

**更确定性的回答**:
```bash
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=1000
```

## 🎯 下一步

现在你已经成功运行了 AI Agent，可以：

1. **深入了解配置** → [配置指南](../configuration/)
2. **学习高级功能** → [教程](../tutorials/)
3. **了解系统架构** → [架构文档](../../architecture/overview/)
4. **参与开发** → [贡献指南](../../development/contributing/)

## ❓ 常见问题

### Q: 如何获取 API 密钥？

**OpenAI**:
1. 访问 https://platform.openai.com/
2. 注册或登录账号
3. 进入 API Keys 页面
4. 创建新的 API 密钥

**Anthropic**:
1. 访问 https://console.anthropic.com/
2. 注册账号
3. 获取 API 密钥

**DeepSeek**:
1. 访问 https://platform.deepseek.com/
2. 注册账号
3. 获取 API 密钥

### Q: 出现 "Invalid API key" 错误怎么办？

1. 检查 `.env` 文件是否存在
2. 确认 API 密钥正确（不包含占位符文本）
3. 验证 API 密钥是否有效（未过期）
4. 确保没有多余的空格或引号

### Q: 如何查看日志？

设置日志级别：
```bash
LOG_LEVEL=DEBUG  # 详细日志
LOG_LEVEL=INFO   # 正常日志（默认）
LOG_LEVEL=ERROR  # 只显示错误
```

### Q: 端口 8000 被占用怎么办？

使用不同的端口：
```bash
chainlit run app.py -w --port 8080
```

### Q: 虚拟环境激活失败？

**macOS/Linux**:
```bash
# 如果使用 zsh
source venv/bin/activate

# 如果使用 bash
. venv/bin/activate
```

**Windows**:
```bash
# PowerShell
venv\Scripts\Activate.ps1

# CMD
venv\Scripts\activate.bat
```

## 🐛 遇到问题？

如果遇到问题：

1. 查看 [故障排查指南](../../operations/troubleshooting/)
2. 搜索 [GitHub Issues](../../issues)
3. 提交新的 Issue 并提供：
   - 错误信息
   - 系统环境（OS、Python 版本）
   - 复现步骤

## 📚 相关文档

- [配置指南](../configuration/) - 详细的配置选项
- [架构概览](../../architecture/overview/) - 了解系统设计
- [API 文档](../../api/) - API 接口说明
- [贡献指南](../../development/contributing/) - 如何贡献代码

---

**需要帮助？** 查看 [完整文档](../../README.md) 或 [提交 Issue](../../issues)

