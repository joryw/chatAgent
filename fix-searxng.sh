#!/bin/bash

################################################################################
# SearXNG 配置修复脚本
# 用途: 修复已部署但配置错误的 SearXNG 实例
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SEARXNG_DIR="${HOME}/searxng-local"

print_header() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header "SearXNG 配置修复"

# 检查目录是否存在
if [ ! -d "$SEARXNG_DIR" ]; then
    print_error "SearXNG 部署目录不存在: $SEARXNG_DIR"
    print_info "请先运行: ./deploy-searxng.sh"
    exit 1
fi

# 停止容器
print_info "停止 SearXNG 容器..."
docker stop searxng 2>/dev/null || true

# 备份旧配置
if [ -f "$SEARXNG_DIR/searxng-data/settings.yml" ]; then
    print_info "备份旧配置..."
    cp "$SEARXNG_DIR/searxng-data/settings.yml" "$SEARXNG_DIR/searxng-data/settings.yml.backup"
    print_success "已备份到: settings.yml.backup"
fi

# 生成新的 secret key
SECRET_KEY=$(python3 -c 'import os; print(os.urandom(24).hex())' 2>/dev/null || openssl rand -hex 24)
print_success "生成新的 secret key"

# 创建正确的 settings.yml
print_info "生成新的配置文件..."
cat > "$SEARXNG_DIR/searxng-data/settings.yml" <<EOF
# SearXNG Configuration for AI Agent
# Fixed configuration - $(date)

use_default_settings: true

general:
  instance_name: "AI Agent Local SearXNG"
  enable_metrics: false

server:
  secret_key: "${SECRET_KEY}"
  limiter: false
  image_proxy: true
  
search:
  safe_search: 1
  autocomplete: ""
  default_lang: "auto"
  formats:
    - html
    - json

ui:
  static_use_hash: true

outgoing:
  request_timeout: 3.0
  max_request_timeout: 10.0
  
enabled_plugins:
  - 'Hash plugin'
  - 'Self Information'
  - 'Tracker URL remover'
EOF

print_success "配置文件已更新"

# 重启容器
print_info "重启 SearXNG 容器..."
cd "$SEARXNG_DIR"
if docker compose version &> /dev/null; then
    docker compose restart
else
    docker-compose restart 2>/dev/null || docker compose restart
fi

# 等待服务启动
print_info "等待服务启动..."
for i in {1..30}; do
    if curl -s "http://localhost:8080" > /dev/null 2>&1; then
        print_success "SearXNG 服务已启动"
        break
    fi
    sleep 1
done

# 验证 JSON API
print_info "验证 JSON API..."
sleep 2
API_RESPONSE=$(curl -s "http://localhost:8080/search?q=test&format=json")
if echo "$API_RESPONSE" | grep -q '"results"'; then
    print_success "JSON API 工作正常！"
    
    print_header "修复完成"
    echo ""
    echo -e "${GREEN}SearXNG 配置已修复并正常运行！${NC}"
    echo ""
    echo -e "${BLUE}📍 测试访问:${NC}"
    echo "   Web 界面: http://localhost:8080"
    echo "   JSON API: http://localhost:8080/search?q=test&format=json"
    echo ""
else
    print_error "JSON API 仍然有问题"
    echo ""
    echo -e "${YELLOW}请查看日志:${NC}"
    echo "   docker logs searxng"
    echo ""
    exit 1
fi
EOF

chmod +x fix-searxng.sh

