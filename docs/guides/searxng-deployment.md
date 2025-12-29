# SearXNG 本地部署指南

> 为 AI 助手启用稳定可靠的联网搜索功能

## 📚 目录

- [为什么需要本地部署](#为什么需要本地部署)
- [前置要求](#前置要求)
- [快速部署](#快速部署)
- [配置说明](#配置说明)
- [验证部署](#验证部署)
- [常见问题](#常见问题)
- [进阶配置](#进阶配置)

## 为什么需要本地部署

公共 SearXNG 实例存在以下问题：
- ❌ 服务不稳定，经常超时
- ❌ 受限流限制，响应慢
- ❌ 无法保证长期可用性
- ❌ 无法定制搜索配置

本地部署的优势：
- ✅ 完全掌控，稳定可靠
- ✅ 无限流限制，响应快
- ✅ 可定制搜索引擎和参数
- ✅ 保护隐私，数据不外泄

## 前置要求

### 系统要求
- **操作系统**: Linux / macOS / Windows (WSL2)
- **内存**: 最低 512MB，推荐 1GB
- **磁盘**: 最低 1GB 可用空间
- **网络**: 能够访问互联网

### 软件要求
- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0 (Docker Desktop 自带)

### 安装 Docker

#### macOS
```bash
# 使用 Homebrew 安装
brew install --cask docker

# 或下载 Docker Desktop
# https://www.docker.com/products/docker-desktop/
```

#### Linux (Ubuntu/Debian)
```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 启动 Docker 服务
sudo systemctl enable docker
sudo systemctl start docker

# 将当前用户加入 docker 组 (避免使用 sudo)
sudo usermod -aG docker $USER

# 重新登录使更改生效
```

#### Windows
```bash
# 安装 WSL2
wsl --install

# 下载并安装 Docker Desktop for Windows
# https://www.docker.com/products/docker-desktop/
```

### 验证 Docker 安装
```bash
# 检查 Docker 版本
docker --version
# 输出示例: Docker version 24.0.0, build ...

# 检查 Docker Compose 版本
docker compose version
# 输出示例: Docker Compose version v2.20.0
```

## 快速部署

### 方式一: 使用项目提供的配置 (推荐)

#### 1. 获取配置文件
项目已提供预配置的模板文件：
- `openspec/changes/update-searxng-local-deployment/docker-compose.yml.example`
- `openspec/changes/update-searxng-local-deployment/settings.yml.example`

#### 2. 创建部署目录
```bash
# 在项目根目录下创建 SearXNG 部署目录
cd /path/to/chatAgent
mkdir -p searxng-deploy/searxng

# 复制配置文件
cp openspec/changes/update-searxng-local-deployment/docker-compose.yml.example \
   searxng-deploy/docker-compose.yml

cp openspec/changes/update-searxng-local-deployment/settings.yml.example \
   searxng-deploy/searxng/settings.yml
```

#### 3. 生成 Secret Key
```bash
# 生成随机 secret key
SECRET=$(openssl rand -hex 32)
echo "Your secret key: $SECRET"

# macOS 用户替换配置
sed -i '' "s/change-this-to-a-random-string/$SECRET/" searxng-deploy/docker-compose.yml

# Linux 用户替换配置
sed -i "s/change-this-to-a-random-string/$SECRET/" searxng-deploy/docker-compose.yml
```

#### 4. 启动服务
```bash
cd searxng-deploy

# 启动容器 (后台运行)
docker compose up -d

# 查看日志 (确认启动成功)
docker compose logs -f searxng
```

#### 5. 验证部署
```bash
# 等待几秒钟，然后测试
sleep 5

# 测试 Web 界面
curl http://localhost:8080/

# 测试 JSON API (重要)
curl "http://localhost:8080/search?q=test&format=json" | jq .

# 如果看到 JSON 格式的搜索结果，说明部署成功！
```

### 方式二: 使用官方配置

```bash
# 1. 下载官方 Docker Compose 配置
mkdir -p ~/searxng
cd ~/searxng

# 2. 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  searxng:
    container_name: searxng
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
      - SEARXNG_SECRET=your-secret-key-here
    restart: unless-stopped
EOF

# 3. 创建配置目录
mkdir -p searxng

# 4. 创建最小配置文件
cat > searxng/settings.yml << 'EOF'
search:
  formats:
    - html
    - json

server:
  limiter: false

general:
  instance_name: "Personal SearXNG"
EOF

# 5. 启动服务
docker compose up -d
```

## 配置说明

### docker-compose.yml 关键配置

```yaml
services:
  searxng:
    image: searxng/searxng:latest  # 使用最新稳定版
    
    ports:
      - "8080:8080"  # 端口映射，可修改左侧端口
    
    volumes:
      - ./searxng:/etc/searxng:rw  # 配置文件挂载
    
    environment:
      # 修改为随机字符串
      - SEARXNG_SECRET=change-this-to-a-random-string
    
    restart: unless-stopped  # 自动重启策略
```

### settings.yml 关键配置

```yaml
# 必需配置
search:
  formats:
    - html
    - json  # 必须启用，用于 API 集成

# 服务器配置
server:
  limiter: false  # 本地使用可禁用限流
  # 如果暴露到公网，建议启用限流

# 通用配置
general:
  instance_name: "Personal SearXNG"
  default_lang: "auto"

# 搜索引擎配置
engines:
  - name: google
    engine: google
  - name: bing
    engine: bing
  - name: duckduckgo
    engine: duckduckgo
```

### 自定义端口

如果 8080 端口被占用，可以修改：

```yaml
# docker-compose.yml
ports:
  - "9090:8080"  # 使用 9090 端口
```

相应地更新环境变量：

```bash
# .env 文件
SEARXNG_URL=http://localhost:9090
```

## 验证部署

### 1. 检查容器状态
```bash
# 查看运行中的容器
docker ps | grep searxng

# 应该看到类似输出:
# CONTAINER ID   IMAGE                    STATUS          PORTS
# abc123def456   searxng/searxng:latest  Up 2 minutes   0.0.0.0:8080->8080/tcp
```

### 2. 检查日志
```bash
# 查看最近的日志
docker compose logs --tail=50 searxng

# 实时查看日志
docker compose logs -f searxng

# 正常启动应该看到:
# searxng | [INFO] ... Server started
# searxng | [INFO] ... Listening on 0.0.0.0:8080
```

### 3. 测试 Web 界面
```bash
# 使用浏览器访问
open http://localhost:8080

# 或使用 curl
curl -I http://localhost:8080
# 应该返回: HTTP/1.1 200 OK
```

### 4. 测试 JSON API (最重要)
```bash
# 测试搜索 API
curl "http://localhost:8080/search?q=python&format=json" | jq .

# 应该返回 JSON 格式的结果，包含:
# {
#   "query": "python",
#   "results": [
#     {
#       "title": "...",
#       "url": "...",
#       "content": "..."
#     }
#   ]
# }
```

### 5. 在 AI 助手中测试
```bash
# 更新环境变量
echo "SEARXNG_URL=http://localhost:8080" >> .env

# 重启应用
# ... 重启你的 AI 助手

# 在聊天界面中:
/search on
# 然后问一个需要联网搜索的问题
```

## 常见问题

### Q1: 容器无法启动

**症状**: `docker compose up -d` 失败或容器立即退出

**排查步骤**:
```bash
# 1. 查看详细日志
docker compose logs searxng

# 2. 检查配置文件语法
docker compose config

# 3. 检查端口占用
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# 4. 检查磁盘空间
df -h
```

**常见原因**:
- ❌ 端口被占用 → 修改端口映射
- ❌ settings.yml 语法错误 → 检查 YAML 格式
- ❌ 权限不足 → 检查目录权限

### Q2: JSON API 不可用

**症状**: 访问 `/search?format=json` 返回错误或 HTML

**解决方案**:
```bash
# 1. 检查 settings.yml 中是否启用了 json 格式
cat searxng/settings.yml | grep -A 3 "formats:"

# 应该看到:
# search:
#   formats:
#     - html
#     - json

# 2. 如果没有，添加配置后重启
docker compose restart searxng

# 3. 验证 JSON API
curl "http://localhost:8080/search?q=test&format=json" | jq .query
```

### Q3: 搜索结果为空

**症状**: API 返回 200 但 results 数组为空

**可能原因**:
1. **搜索引擎被封禁**: 某些地区无法访问 Google 等
2. **网络问题**: 容器无法访问外网
3. **引擎配置错误**: settings.yml 中引擎配置有误

**解决方案**:
```bash
# 1. 测试网络连接
docker exec searxng ping -c 3 google.com

# 2. 检查引擎配置
cat searxng/settings.yml | grep -A 5 "engines:"

# 3. 尝试使用不同的搜索引擎
# 在 settings.yml 中启用 DuckDuckGo, Bing 等

# 4. 查看详细日志
docker compose logs searxng | grep ERROR
```

### Q4: 性能慢或超时

**症状**: 搜索请求超过 5 秒或经常超时

**优化方案**:
```yaml
# 1. 增加资源限制 (docker-compose.yml)
deploy:
  resources:
    limits:
      cpus: '2.0'        # 增加 CPU
      memory: 1024M      # 增加内存

# 2. 调整超时时间 (settings.yml)
outgoing:
  request_timeout: 5.0  # 增加超时时间
  max_request_timeout: 15.0

# 3. 减少启用的搜索引擎数量
# 禁用不常用的引擎

# 4. 添加 Redis 缓存
# 参考进阶配置部分
```

### Q5: 无法从其他机器访问

**症状**: 只能在本机访问，局域网其他设备无法访问

**解决方案**:
```yaml
# 修改 docker-compose.yml
ports:
  - "0.0.0.0:8080:8080"  # 监听所有网络接口

# 或指定具体 IP
ports:
  - "192.168.1.100:8080:8080"

# 重启服务
docker compose restart

# 更新环境变量
SEARXNG_URL=http://192.168.1.100:8080
```

### Q6: 更新 SearXNG 版本

```bash
# 1. 拉取最新镜像
docker compose pull

# 2. 重新创建容器
docker compose up -d

# 3. 清理旧镜像
docker image prune
```

## 进阶配置

### 1. 添加 Redis 缓存 (提升性能)

```yaml
# docker-compose.yml
services:
  searxng:
    # ... 现有配置 ...
    depends_on:
      - redis
  
  redis:
    container_name: searxng-redis
    image: redis:alpine
    command: redis-server --save 30 1 --loglevel warning
    restart: unless-stopped
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

```yaml
# settings.yml
redis:
  url: redis://redis:6379/0
```

### 2. 启用 HTTPS (使用反向代理)

```nginx
# nginx.conf 示例
server {
    listen 443 ssl;
    server_name search.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 自定义搜索引擎权重

```yaml
# settings.yml
engines:
  - name: google
    engine: google
    weight: 2  # 提高 Google 结果权重
  
  - name: wikipedia
    engine: wikipedia
    weight: 3  # 优先显示维基百科
  
  - name: stackoverflow
    engine: stackoverflow
    weight: 1.5  # 技术问题优先
```

### 4. 配置日志记录

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

# 查看日志
docker compose logs -f --tail=100 searxng
```

### 5. 设置自动备份

```bash
# backup.sh
#!/bin/bash
BACKUP_DIR=~/searxng-backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp -r searxng/settings.yml "$BACKUP_DIR/settings_$DATE.yml"
echo "Backup saved to $BACKUP_DIR/settings_$DATE.yml"

# 添加到 crontab
crontab -e
# 每天凌晨 2 点备份
0 2 * * * /path/to/backup.sh
```

## 维护和管理

### 日常维护

```bash
# 查看服务状态
docker compose ps

# 查看资源使用
docker stats searxng

# 重启服务
docker compose restart

# 停止服务
docker compose stop

# 完全移除 (包括数据)
docker compose down -v
```

### 故障恢复

```bash
# 1. 停止服务
docker compose down

# 2. 备份配置
cp -r searxng searxng.backup

# 3. 清理并重启
docker compose up -d --force-recreate

# 4. 如果需要,恢复配置
cp -r searxng.backup/* searxng/
docker compose restart
```

## 相关资源

- 📖 [SearXNG 官方文档](https://docs.searxng.org/)
- 🐙 [SearXNG GitHub 仓库](https://github.com/searxng/searxng)
- 🐳 [Docker Hub - SearXNG](https://hub.docker.com/r/searxng/searxng)
- 💬 [SearXNG Matrix 频道](https://matrix.to/#/#searxng:matrix.org)

## 获取帮助

如果遇到问题:
1. 查看本文档的[常见问题](#常见问题)部分
2. 检查 SearXNG 日志: `docker compose logs searxng`
3. 访问[项目故障排查文档](../troubleshooting/searxng.md)
4. 在项目 Issues 中搜索类似问题

---

**部署完成后,别忘了在 `.env` 文件中更新 `SEARXNG_URL` 配置！** 🎉

