# SearXNG 故障排查指南

本文档提供 SearXNG 部署和使用中常见问题的诊断和解决方案。

## 📋 目录

- [快速诊断](#快速诊断)
- [部署问题](#部署问题)
- [连接问题](#连接问题)
- [配置问题](#配置问题)
- [性能问题](#性能问题)
- [搜索问题](#搜索问题)
- [日志分析](#日志分析)

## 快速诊断

### 一键诊断脚本

```bash
#!/bin/bash
# searxng-diagnose.sh - SearXNG 快速诊断脚本

echo "=== SearXNG 诊断工具 ==="
echo ""

# 1. 检查 Docker
echo "1. 检查 Docker 状态..."
if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装: $(docker --version)"
else
    echo "❌ Docker 未安装"
    exit 1
fi

# 2. 检查容器状态
echo ""
echo "2. 检查容器状态..."
if docker ps | grep -q searxng; then
    echo "✅ SearXNG 容器正在运行"
    docker ps | grep searxng
else
    echo "❌ SearXNG 容器未运行"
    echo "尝试启动: docker compose up -d"
fi

# 3. 检查端口
echo ""
echo "3. 检查端口..."
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ 端口 8080 可访问"
else
    echo "❌ 端口 8080 无法访问"
    echo "检查: lsof -i :8080"
fi

# 4. 测试 JSON API
echo ""
echo "4. 测试 JSON API..."
RESPONSE=$(curl -s "http://localhost:8080/search?q=test&format=json")
if echo "$RESPONSE" | grep -q '"query"'; then
    echo "✅ JSON API 工作正常"
    echo "$RESPONSE" | jq -r '.query'
else
    echo "❌ JSON API 返回异常"
    echo "响应: $RESPONSE"
fi

# 5. 检查日志
echo ""
echo "5. 最近的错误日志..."
docker compose logs --tail=20 searxng 2>&1 | grep -i error || echo "✅ 无错误日志"

echo ""
echo "=== 诊断完成 ==="
```

### 使用诊断脚本

```bash
# 1. 保存脚本
curl -o searxng-diagnose.sh https://your-repo/searxng-diagnose.sh

# 2. 添加执行权限
chmod +x searxng-diagnose.sh

# 3. 运行诊断
./searxng-diagnose.sh
```

## 部署问题

### 问题 1: 容器无法启动

**症状**:
```bash
$ docker compose up -d
Error: Cannot start container ...
```

**诊断步骤**:

```bash
# 1. 查看详细错误
docker compose up

# 2. 检查 Docker 服务
systemctl status docker  # Linux
# 或检查 Docker Desktop 是否运行

# 3. 检查镜像
docker images | grep searxng

# 4. 检查配置文件
docker compose config
```

**常见原因和解决方案**:

#### 原因 1: 端口被占用
```bash
# 检查端口占用
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# 解决: 修改端口
# 在 docker-compose.yml 中:
ports:
  - "9090:8080"  # 改用 9090
```

#### 原因 2: Docker 服务未启动
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# 启动 Docker Desktop
```

#### 原因 3: 权限问题
```bash
# Linux: 将用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录后生效
newgrp docker
```

#### 原因 4: 磁盘空间不足
```bash
# 检查磁盘空间
df -h

# 清理 Docker 缓存
docker system prune -a
```

### 问题 2: 容器启动后立即退出

**诊断**:
```bash
# 查看容器状态
docker ps -a | grep searxng

# 查看退出日志
docker compose logs searxng
```

**常见原因**:

#### 配置文件语法错误
```bash
# 验证 YAML 语法
docker compose config

# 检查 settings.yml
cat searxng/settings.yml | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)"
```

#### 权限问题
```bash
# 检查配置目录权限
ls -la searxng/

# 修复权限
chmod 755 searxng
chmod 644 searxng/settings.yml
```

## 连接问题

### 问题 3: 无法访问 Web 界面

**症状**:
- `curl http://localhost:8080` 超时或拒绝连接

**诊断**:
```bash
# 1. 确认容器运行
docker ps | grep searxng

# 2. 确认端口映射
docker port searxng

# 3. 测试容器内部
docker exec searxng curl -I http://localhost:8080

# 4. 检查防火墙
# macOS
sudo pfctl -sr | grep 8080

# Linux
sudo iptables -L -n | grep 8080
```

**解决方案**:

```bash
# 如果容器内部可访问但主机无法访问
# 检查 docker-compose.yml 端口映射
ports:
  - "0.0.0.0:8080:8080"  # 确保绑定到所有接口

# 重启容器
docker compose restart
```

### 问题 4: AI 助手无法连接到 SearXNG

**症状**:
- AI 助手报告搜索服务不可用
- 环境变量已正确配置

**诊断**:
```bash
# 1. 从 AI 助手容器/进程测试
# (如果 AI 助手在容器中运行)
docker exec ai-assistant curl http://host.docker.internal:8080

# 2. 检查网络连接
ping localhost

# 3. 检查 DNS 解析
nslookup localhost
```

**解决方案**:

```bash
# 场景 1: AI 助手在同一主机
SEARXNG_URL=http://localhost:8080

# 场景 2: AI 助手在 Docker 容器中
# 使用 Docker 特殊 DNS
SEARXNG_URL=http://host.docker.internal:8080

# 场景 3: AI 助手在不同主机
# 使用主机 IP
SEARXNG_URL=http://192.168.1.100:8080

# 场景 4: 两者在同一 Docker 网络
# 使用容器名
SEARXNG_URL=http://searxng:8080
```

## 配置问题

### 问题 5: JSON API 不工作

**症状**:
- 访问 `/search?format=json` 返回 HTML 或错误

**诊断**:
```bash
# 测试 JSON API
curl -v "http://localhost:8080/search?q=test&format=json"

# 检查响应头
# 应该包含: Content-Type: application/json
```

**解决方案**:

```bash
# 1. 检查 settings.yml
cat searxng/settings.yml | grep -A 3 "formats:"

# 必须包含:
search:
  formats:
    - html
    - json  # 确保存在

# 2. 如果缺失,添加配置
vim searxng/settings.yml

# 3. 重启容器
docker compose restart searxng

# 4. 等待几秒后重试
sleep 5
curl "http://localhost:8080/search?q=test&format=json" | jq .
```

### 问题 6: 搜索结果为空

**症状**:
- API 返回成功但 `results` 数组为空

**诊断**:
```bash
# 1. 测试不同的查询
curl "http://localhost:8080/search?q=python&format=json" | jq '.results | length'

# 2. 检查启用的搜索引擎
cat searxng/settings.yml | grep -A 50 "engines:"

# 3. 查看详细日志
docker compose logs searxng | grep -i "search\|engine\|error"

# 4. 测试容器网络
docker exec searxng ping -c 3 google.com
```

**常见原因**:

#### 原因 1: 网络访问受限
```bash
# 某些地区无法访问 Google 等搜索引擎
# 解决: 使用可访问的搜索引擎

# settings.yml
engines:
  - name: duckduckgo
    engine: duckduckgo
  - name: bing
    engine: bing
  # 禁用无法访问的引擎
  - name: google
    disabled: true
```

#### 原因 2: 搜索引擎全部禁用
```bash
# 检查 settings.yml
# 确保至少有一个引擎启用

engines:
  - name: duckduckgo
    engine: duckduckgo
    # disabled: false  # 确保未禁用
```

#### 原因 3: 超时设置太短
```yaml
# settings.yml
outgoing:
  request_timeout: 5.0  # 增加超时时间
  max_request_timeout: 15.0
```

## 性能问题

### 问题 7: 搜索响应慢

**症状**:
- 搜索请求超过 10 秒
- AI 助手报告搜索超时

**诊断**:
```bash
# 1. 测试响应时间
time curl -s "http://localhost:8080/search?q=test&format=json" > /dev/null

# 2. 检查容器资源使用
docker stats searxng

# 3. 查看并发请求数
docker logs searxng | grep "request" | tail -20
```

**优化方案**:

#### 方案 1: 增加资源限制
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1024M
    reservations:
      cpus: '0.5'
      memory: 256M
```

#### 方案 2: 减少搜索引擎数量
```yaml
# settings.yml
# 只启用必要的快速引擎
engines:
  - name: duckduckgo  # 快速
    engine: duckduckgo
  - name: bing        # 快速
    engine: bing
  # 禁用慢速引擎
  # - name: wikipedia
  #   disabled: true
```

#### 方案 3: 调整超时配置
```yaml
# settings.yml
outgoing:
  request_timeout: 3.0  # 减少超时等待
  max_request_timeout: 8.0
  pool_connections: 100
  pool_maxsize: 20
```

#### 方案 4: 添加 Redis 缓存
```yaml
# docker-compose.yml
services:
  searxng:
    depends_on:
      - redis
  
  redis:
    image: redis:alpine
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

### 问题 8: 内存使用过高

**诊断**:
```bash
# 监控内存使用
docker stats searxng --no-stream

# 查看详细信息
docker inspect searxng | jq '.[0].HostConfig.Memory'
```

**解决方案**:
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M  # 限制最大内存
```

## 搜索问题

### 问题 9: 特定搜索引擎不工作

**诊断**:
```bash
# 1. 查看日志中的引擎错误
docker logs searxng | grep "engine"

# 2. 测试特定引擎
# 在 Web 界面使用快捷键: !g (Google), !ddg (DuckDuckGo)
```

**解决方案**:
```yaml
# settings.yml
# 禁用问题引擎
engines:
  - name: problematic_engine
    disabled: true
```

### 问题 10: 搜索结果质量差

**优化策略**:
```yaml
# settings.yml
# 1. 调整引擎权重
engines:
  - name: google
    engine: google
    weight: 2  # 提高权重
  
  - name: wikipedia
    engine: wikipedia
    weight: 3  # 优先显示维基
  
  - name: bing
    engine: bing
    weight: 1  # 降低权重

# 2. 启用结果去重
enabled_plugins:
  - 'Hash plugin'

# 3. 配置语言偏好
general:
  default_lang: "zh-CN"  # 中文结果
```

## 日志分析

### 查看日志

```bash
# 查看实时日志
docker compose logs -f searxng

# 查看最近 100 行
docker compose logs --tail=100 searxng

# 查看特定时间
docker compose logs --since 10m searxng

# 导出日志
docker compose logs searxng > searxng.log
```

### 常见日志模式

#### 正常启动
```
[INFO] Server started
[INFO] Listening on 0.0.0.0:8080
[INFO] Engine initialized: google
[INFO] Engine initialized: bing
```

#### 配置错误
```
[ERROR] Failed to load settings.yml
[ERROR] Invalid YAML syntax
[ERROR] Unknown configuration key
```

#### 搜索引擎错误
```
[WARNING] Engine 'google' failed
[ERROR] Connection timeout to bing.com
[WARNING] No results from wikipedia
```

#### 网络问题
```
[ERROR] DNS resolution failed
[ERROR] Connection refused
[ERROR] SSL certificate verification failed
```

### 日志级别调整

```yaml
# settings.yml
server:
  log_level: "DEBUG"  # ERROR, WARNING, INFO, DEBUG
```

## 高级诊断

### 容器内部调试

```bash
# 进入容器
docker exec -it searxng /bin/sh

# 在容器内测试
wget -O- http://localhost:8080
curl http://localhost:8080/search?q=test&format=json

# 检查配置
cat /etc/searxng/settings.yml

# 检查进程
ps aux | grep searxng
```

### 网络调试

```bash
# 检查容器网络
docker network ls
docker network inspect bridge

# 测试 DNS 解析
docker exec searxng nslookup google.com

# 测试外部连接
docker exec searxng wget -O- https://www.google.com
```

### 性能分析

```bash
# 启用详细日志
# settings.yml: log_level: "DEBUG"

# 分析响应时间
docker logs searxng | grep "timing" | tail -20

# 监控系统资源
docker stats --no-stream
```

## 获取帮助

如果以上方法都无法解决问题:

1. **收集诊断信息**:
```bash
# 运行诊断脚本
./searxng-diagnose.sh > diagnosis.txt

# 导出日志
docker compose logs searxng > searxng.log

# 导出配置
cat searxng/settings.yml > settings-export.yml
```

2. **提交 Issue**:
- 访问项目 Issues 页面
- 搜索是否有类似问题
- 提供诊断信息、日志和配置

3. **社区支持**:
- [SearXNG Matrix 频道](https://matrix.to/#/#searxng:matrix.org)
- [SearXNG GitHub Discussions](https://github.com/searxng/searxng/discussions)

---

**记住**: 90% 的问题都是配置导致的。仔细检查 `settings.yml` 和 `docker-compose.yml`! 🔍

