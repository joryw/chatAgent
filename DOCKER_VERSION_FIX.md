# Docker 版本问题解决方案

## 问题描述

错误信息：
```
Error response from daemon: client version 1.42 is too old. 
Minimum supported API version is 1.44, please upgrade your client to a newer version
```

## 原因分析

系统中存在两个 Docker Compose 版本：
- `docker-compose` (旧版独立工具): v2.6.0，使用 API 1.42 ❌
- `docker compose` (新版内置命令): v2.40.3，使用 API 1.44+ ✅

## ✅ 解决方案（已应用）

### 方案 1: 使用内置命令（推荐，已修复）

脚本已更新为自动使用 `docker compose` (空格) 而不是 `docker-compose` (连字符)。

**现在可以直接使用：**
```bash
./deploy-searxng.sh
```

### 方案 2: 手动操作时使用正确的命令

如果手动操作 Docker Compose，请使用：

```bash
# ✅ 正确 - 使用内置命令
docker compose up -d
docker compose down
docker compose logs -f

# ❌ 错误 - 旧版独立工具
docker-compose up -d
```

### 方案 3: 升级或卸载旧版 docker-compose（可选）

如果想彻底解决，可以卸载旧版：

```bash
# 查找旧版位置
which docker-compose

# 卸载方式取决于安装方式
# Homebrew 安装的
brew uninstall docker-compose

# pip 安装的
pip uninstall docker-compose

# 手动安装的
sudo rm /usr/local/bin/docker-compose
```

## 版本对照表

| Docker Compose 版本 | API 版本 | Docker Engine | 状态 |
|-------------------|---------|---------------|------|
| v2.6.0 及以下 | 1.42 | 21.x | ❌ 太旧 |
| v2.10.0+ | 1.43 | 22.x | ⚠️ 即将过时 |
| v2.15.0+ | 1.44 | 23.x+ | ✅ 支持 |
| v2.40.0+ | 1.47 | 29.x | ✅ 推荐 |

## 验证修复

```bash
# 1. 检查使用的是哪个版本
docker compose version
# 应该显示: Docker Compose version v2.40.3-desktop.1

# 2. 运行部署脚本
./deploy-searxng.sh

# 3. 如果成功，应该看到：
# ✅ Docker Compose 已安装 (使用内置版本)
```

## 相关文档

- [Docker Compose v1 vs v2](https://docs.docker.com/compose/migrate/)
- [Docker API 版本兼容性](https://docs.docker.com/engine/api/)

## 问题已解决

✅ 脚本已更新，现在会自动使用正确的 `docker compose` 命令。

