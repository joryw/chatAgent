# Docker 部署指南

本指南介绍如何使用 Docker 部署完整的 AI Agent + SearXNG 系统。

## 🚀 三种部署方式

### 方式 1: 一键脚本部署 (推荐)

**最简单快速**，自动完成所有配置。

```bash
# 部署 SearXNG
./deploy-searxng.sh

# 一键启动全部服务
./start-all.sh
```

#### 优点
- ✅ 零配置，全自动
- ✅ 自动验证部署
- ✅ 智能错误诊断
- ✅ 适合本地开发

---

### 方式 2: 仅 Docker Compose 部署 SearXNG

**灵活性高**，手动控制每一步。

#### 步骤

1. **创建部署目录**
```bash
mkdir -p ~/searxng-local
cd ~/searxng-local
```

2. **创建 docker-compose.yml**
```yaml
version: '3.8'

services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng-data:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
      - SEARXNG_PORT=8080
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

3. **创建配置目录和 settings.yml**
```bash
mkdir -p searxng-data

# 生成 secret key
SECRET_KEY=$(python3 -c 'import os; print(os.urandom(24).hex())')

# 创建 settings.yml
cat > searxng-data/settings.yml <<EOF
server:
  secret_key: "${SECRET_KEY}"

search:
  formats:
    - html
    - json  # 重要: 启用 JSON API
  safe_search: 1
EOF
```

4. **启动服务**
```bash
docker compose up -d
```

5. **验证部署**
```bash
# 检查容器状态
docker ps -f name=searxng

# 测试 JSON API
curl "http://localhost:8080/search?q=test&format=json" | jq .
```

6. **配置 AI Agent**
```bash
cd /path/to/chatAgent

# 更新 .env
cat >> .env <<EOF
SEARXNG_URL=http://localhost:8080
SEARCH_ENABLED=true
EOF

# 启动 AI Agent
source venv/bin/activate
chainlit run app.py
```

#### 优点
- ✅ 配置灵活可定制
- ✅ 便于理解每个步骤
- ✅ 适合生产环境

---

### 方式 3: 完整容器化部署

**生产级部署**，SearXNG 和 AI Agent 都在容器中。

#### 步骤

1. **准备配置文件**
```bash
cd /path/to/chatAgent

# 确保 .env 文件已配置
cp .env.example .env
# 编辑 .env 添加 API keys
```

2. **初始化 SearXNG 配置**
```bash
mkdir -p searxng-data

# 生成 secret key
SECRET_KEY=$(python3 -c 'import os; print(os.urandom(24).hex())')

# 创建 settings.yml
cat > searxng-data/settings.yml <<EOF
server:
  secret_key: "${SECRET_KEY}"
search:
  formats:
    - html
    - json
EOF
```

3. **使用完整 docker-compose 启动**
```bash
# 使用提供的完整配置文件
docker-compose -f docker-compose.full.yml up -d
```

4. **查看日志**
```bash
# 查看 SearXNG 日志
docker logs searxng -f

# 如果启用了 AI Agent 容器
docker logs ai-agent -f
```

5. **访问服务**
- SearXNG: http://localhost:8080
- AI Agent: http://localhost:8000

#### 优点
- ✅ 完全容器化
- ✅ 易于部署到服务器
- ✅ 资源隔离
- ✅ 便于扩展

#### 注意事项
- AI Agent 容器默认是注释的，需要手动取消注释
- 确保 `.env` 文件在项目根目录
- 首次构建可能需要几分钟

---

## 🔧 常用管理命令

### SearXNG 管理

```bash
# 启动
docker start searxng

# 停止
docker stop searxng

# 重启
docker restart searxng

# 查看日志
docker logs searxng -f

# 查看状态
docker ps -f name=searxng

# 删除容器
docker stop searxng && docker rm searxng

# 完全清理 (包括数据)
cd ~/searxng-local
docker-compose down -v
rm -rf searxng-data
```

### AI Agent 管理 (如使用容器化部署)

```bash
# 构建镜像
docker build -t ai-agent .

# 启动容器
docker run -d \
  --name ai-agent \
  --env-file .env \
  -p 8000:8000 \
  ai-agent

# 停止
docker stop ai-agent

# 查看日志
docker logs ai-agent -f
```

---

## 🛠️ 配置自定义

### 修改 SearXNG 端口

**方式 1: 使用脚本**
```bash
SEARXNG_PORT=9090 ./deploy-searxng.sh
```

**方式 2: 手动修改**
```yaml
# docker-compose.yml
ports:
  - "9090:8080"  # 主机端口:容器端口
```

记得同时更新 AI Agent 的 `.env`:
```bash
SEARXNG_URL=http://localhost:9090
```

### 添加自定义搜索引擎

编辑 `searxng-data/settings.yml`:

```yaml
engines:
  - name: google
    disabled: false
  - name: bing  
    disabled: false
  - name: duckduckgo
    disabled: false
  
  # 添加更多引擎
  - name: github
    disabled: false
  - name: stackoverflow
    disabled: false
```

修改后重启:
```bash
docker restart searxng
```

---

## 📊 监控和维护

### 健康检查

```bash
# 使用内置验证脚本
bash openspec/changes/archive/2025-12-26-update-searxng-local-deployment/verify-searxng.sh

# 或手动检查
curl -s http://localhost:8080/healthz
```

### 资源监控

```bash
# 查看容器资源使用
docker stats searxng

# 限制资源使用 (在 docker-compose.yml 中)
services:
  searxng:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

### 日志管理

```bash
# 限制日志大小
services:
  searxng:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 🔒 安全建议

### 1. 更改默认密钥
```yaml
# settings.yml
server:
  secret_key: "use-a-strong-random-key"  # 必须修改!
```

### 2. 限制网络访问
```yaml
# docker-compose.yml
ports:
  - "127.0.0.1:8080:8080"  # 只允许本地访问
```

### 3. 使用 HTTPS (生产环境)
```yaml
environment:
  - SEARXNG_BASE_URL=https://your-domain.com/
```

配合 Nginx 反向代理使用。

---

## 🐛 故障排查

### 容器无法启动
```bash
# 查看详细日志
docker logs searxng --tail 100

# 检查端口占用
lsof -i :8080

# 重新创建容器
docker-compose down
docker-compose up -d
```

### JSON API 不可用
```bash
# 1. 检查配置
cat ~/searxng-local/searxng-data/settings.yml | grep -A 3 "search:"

# 2. 确认包含 'json'
# search:
#   formats:
#     - json

# 3. 重启容器
docker restart searxng
```

### 搜索无结果
```bash
# 测试特定引擎
curl "http://localhost:8080/search?q=test&format=json&engines=google"

# 检查引擎状态 (访问 Web 界面)
open http://localhost:8080/stats
```

---

## 📚 相关文档

- [SearXNG 部署指南](../searxng-deployment.md)
- [SearXNG 故障排查](../troubleshooting/searxng.md)
- [配置指南](../configuration/)

---

## 💡 最佳实践

1. **开发环境**: 使用 `./start-all.sh` 一键启动
2. **生产环境**: 使用 `docker-compose.full.yml` 完整部署
3. **定期更新**: `docker pull searxng/searxng:latest`
4. **备份配置**: 定期备份 `searxng-data/` 目录
5. **监控日志**: 设置日志轮转，避免磁盘占满

---

**需要帮助?** 查看 [故障排查指南](../troubleshooting/searxng.md) 或提交 Issue。

