# SearXNG 搜索引擎设置指南

## 概述

本指南介绍如何为 AI Agent 配置 SearXNG 搜索引擎。SearXNG 是一个开源的元搜索引擎，可以聚合多个搜索源的结果，同时保护用户隐私。

## 选项 1: 使用公共实例（快速开始）

### 可用的公共实例

以下是一些可用的公共 SearXNG 实例：

1. **searx.be** - https://searx.be
2. **search.bus-hit.me** - https://search.bus-hit.me  
3. **searx.tiekoetter.com** - https://searx.tiekoetter.com
4. **paulgo.io** - https://paulgo.io

### 配置步骤

1. 在 `.env` 文件中设置 SearXNG URL：

```bash
SEARXNG_URL=https://searx.be
```

2. 启动应用并在聊天界面启用搜索开关

### 注意事项

⚠️ **公共实例的限制：**
- 可能不稳定或暂时不可用
- 可能有速率限制
- SSL 证书可能存在问题
- 不保证长期可用性

💡 **建议：** 对于生产环境，强烈建议部署自己的 SearXNG 实例。

## 选项 2: Docker 部署（推荐）

### 前提条件

- Docker 和 Docker Compose 已安装
- 有公网 IP 或域名（可选，用于远程访问）

### 快速部署

1. **创建 docker-compose.yml**

```yaml
version: '3.7'

services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    restart: unless-stopped
```

2. **创建配置目录**

```bash
mkdir -p searxng
```

3. **创建配置文件** `searxng/settings.yml`

```yaml
general:
  debug: false
  instance_name: "My SearXNG"

search:
  safe_search: 1
  autocomplete: ""
  default_lang: "auto"
  formats:
    - html
    - json

server:
  port: 8080
  bind_address: "0.0.0.0"
  secret_key: "your-secret-key-here"  # 请更改为随机字符串
  limiter: false
  image_proxy: true

ui:
  static_use_hash: true
  default_theme: simple
  default_locale: zh-CN

engines:
  - name: google
    engine: google
    shortcut: go
    disabled: false
    
  - name: bing
    engine: bing
    shortcut: bi
    disabled: false
    
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    disabled: false
```

4. **启动服务**

```bash
docker-compose up -d
```

5. **验证服务**

访问 http://localhost:8080 查看是否正常运行

6. **配置 AI Agent**

在 `.env` 文件中设置：

```bash
SEARXNG_URL=http://localhost:8080
```

### 生产环境部署

对于生产环境，建议：

1. **使用 HTTPS**
   - 配置 Nginx 反向代理
   - 使用 Let's Encrypt 获取 SSL 证书

2. **启用速率限制**
   ```yaml
   server:
     limiter: true
   ```

3. **配置防火墙**
   - 只允许必要的端口访问

4. **定期更新**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## 选项 3: 手动安装

### Ubuntu/Debian

```bash
# 安装依赖
sudo apt update
sudo apt install -y python3-pip python3-venv git

# 克隆仓库
git clone https://github.com/searxng/searxng.git
cd searxng

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装
pip install -e .

# 运行
export SEARXNG_SETTINGS_PATH=settings.yml
python searx/webapp.py
```

## 测试搜索功能

使用项目提供的测试脚本：

```bash
cd /path/to/chatAgent
source venv/bin/activate
python test_search.py
```

预期输出：

```
✅ Found 5 results in 1.23s

Results:
1. Python (programming language) - Wikipedia
   URL: https://en.wikipedia.org/wiki/Python_(programming_language)
   Content: Python is a high-level, interpreted programming language...
```

## 故障排查

### 问题 1: 连接超时

**症状：** `Search request timed out after 5s`

**解决方案：**
- 检查 SearXNG 服务是否运行
- 增加超时时间：`SEARCH_TIMEOUT=10.0`
- 检查网络连接

### 问题 2: SSL 证书错误

**症状：** `certificate verify failed`

**解决方案：**
- 使用 HTTP 而不是 HTTPS（仅限本地测试）
- 配置正确的 SSL 证书
- 使用其他公共实例

### 问题 3: 无搜索结果

**症状：** `No results found`

**解决方案：**
- 检查 SearXNG 配置中的搜索引擎是否启用
- 尝试不同的搜索查询
- 查看 SearXNG 日志：`docker-compose logs -f`

### 问题 4: 速率限制

**症状：** `HTTP 429 Too Many Requests`

**解决方案：**
- 如果使用公共实例，切换到其他实例
- 部署自己的实例
- 在 SearXNG 配置中调整速率限制

## 高级配置

### 自定义搜索引擎

编辑 `settings.yml`：

```yaml
engines:
  - name: github
    engine: github
    shortcut: gh
    disabled: false
    
  - name: stackoverflow
    engine: stackoverflow
    shortcut: so
    disabled: false
```

### 配置代理

如果需要通过代理访问搜索引擎：

```yaml
outgoing:
  request_timeout: 3.0
  proxies:
    http: http://proxy:8080
    https: http://proxy:8080
```

### 启用自动补全

```yaml
search:
  autocomplete: "google"
```

## 安全建议

1. **更改默认密钥**
   ```yaml
   server:
     secret_key: "your-random-secret-key"
   ```

2. **启用速率限制**
   ```yaml
   server:
     limiter: true
   ```

3. **使用 HTTPS**
   - 配置 SSL 证书
   - 强制 HTTPS 重定向

4. **限制访问**
   - 使用防火墙规则
   - 配置 IP 白名单

## 参考资源

- [SearXNG 官方文档](https://docs.searxng.org/)
- [SearXNG GitHub](https://github.com/searxng/searxng)
- [公共实例列表](https://searx.space/)
- [Docker Hub](https://hub.docker.com/r/searxng/searxng)

## 获取帮助

如果遇到问题：

1. 查看 [SearXNG 文档](https://docs.searxng.org/)
2. 搜索 [GitHub Issues](https://github.com/searxng/searxng/issues)
3. 加入 [SearXNG 社区](https://matrix.to/#/#searxng:matrix.org)

