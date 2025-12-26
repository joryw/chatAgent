# 联网搜索功能快速启动指南

## 🚀 5 分钟快速开始

### 步骤 1: 配置环境变量

在 `.env` 文件中添加（如果还没有 `.env` 文件，从 `env.example` 复制）：

```bash
# 搜索配置
SEARXNG_URL=https://searx.be
SEARCH_ENABLED=false  # 默认关闭，用户可在 UI 中启用
```

### 步骤 2: 安装依赖

如果是首次使用，确保安装了 httpx：

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 步骤 3: 启动应用

```bash
chainlit run app.py -w
```

### 步骤 4: 启用搜索

1. 打开浏览器访问 http://localhost:8000
2. 在聊天框中输入命令：`/search on`

### 步骤 5: 开始提问

尝试以下问题：

- "今天的天气怎么样？"
- "最新的 AI 新闻"
- "Python 3.12 有什么新特性？"

---

## 📝 使用示例

### 示例 1: 查询实时信息

**用户：** 2024年最新的人工智能发展趋势是什么？

**系统：**
```
🔍 正在搜索相关信息...
✅ 找到 5 条搜索结果
```

**AI 回答：**
```
根据搜索结果，2024年人工智能的主要发展趋势包括：

1. **生成式 AI 的广泛应用** [1] - 大语言模型在各行业的深度集成
2. **多模态模型的突破** [2] - 图像、文本、音频的统一处理
3. **AI 安全与伦理** [3] - 更多关注 AI 的安全性和可解释性
...

### 🔍 搜索来源

1. [2024 AI Trends Report](https://example.com/ai-trends-2024)
   来源: `example.com`
   摘要: 详细分析了2024年人工智能的发展趋势...

2. [Latest AI News](https://example.com/ai-news)
   来源: `example.com`
   摘要: 最新的人工智能新闻和技术突破...
```

### 示例 2: 技术问题

**用户：** Python 3.12 有哪些新特性？

系统会自动搜索最新的 Python 文档和技术文章，并基于搜索结果提供准确的答案。

---

## 🔧 常见问题

### Q1: 如何启用搜索？

**A:** 在聊天框中输入命令 `/search on`，要关闭搜索输入 `/search off`。

### Q2: 搜索很慢怎么办？

**A:** 
- 公共 SearXNG 实例可能较慢或不稳定
- 建议部署自己的 SearXNG 实例（见下文）
- 可以调整超时时间：`SEARCH_TIMEOUT=10.0`

### Q3: 搜索失败了怎么办？

**A:** 
- 系统会自动降级到无搜索模式
- AI 会基于自身知识回答
- 不影响正常对话

### Q4: 如何关闭搜索？

**A:** 
- 在聊天框中输入命令 `/search off`
- 或重启应用（搜索默认是关闭的）

---

## 🐳 部署自己的 SearXNG（推荐）

### 使用 Docker（最简单）

1. **创建 docker-compose.yml**

```yaml
version: '3.7'

services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    restart: unless-stopped
```

2. **启动服务**

```bash
docker-compose up -d
```

3. **更新配置**

在 `.env` 中：
```bash
SEARXNG_URL=http://localhost:8080
```

4. **重启应用**

```bash
# 停止当前应用（Ctrl+C）
chainlit run app.py -w
```

### 验证部署

访问 http://localhost:8080 应该能看到 SearXNG 搜索界面。

---

## 📚 更多资源

- **完整文档：** [docs/guides/searxng-setup.md](docs/guides/searxng-setup.md)
- **配置说明：** [README.md](README.md)
- **故障排查：** 见完整文档中的故障排查部分

---

## 💡 提示

1. **首次使用建议使用公共实例快速体验**
2. **生产环境强烈建议自部署 SearXNG**
3. **搜索结果质量取决于 SearXNG 配置**
4. **可以根据需要调整搜索参数**

---

## 🎉 开始使用

现在你已经准备好使用联网搜索功能了！

尝试问一些需要实时信息的问题，看看 AI 如何利用搜索结果为你提供更准确、更及时的答案。

**祝使用愉快！** 🚀

