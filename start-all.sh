#!/bin/bash

################################################################################
# 一键启动脚本 - 同时启动 SearXNG 和 AI Agent
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SEARXNG_DIR="${HOME}/searxng-local"
CHATBOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

################################################################################
# 主流程
################################################################################

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          🚀 一键启动 SearXNG + AI Agent                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. 检查 SearXNG 是否已部署
print_header "检查 SearXNG 服务"

if [ ! -d "$SEARXNG_DIR" ]; then
    print_error "SearXNG 尚未部署"
    echo ""
    echo -e "${YELLOW}请先运行部署脚本:${NC}"
    echo "  ./deploy-searxng.sh"
    echo ""
    exit 1
fi

# 2. 启动 SearXNG (如果未运行)
if docker ps --format '{{.Names}}' | grep -q '^searxng$'; then
    print_success "SearXNG 已在运行"
else
    print_info "启动 SearXNG 容器..."
    cd "$SEARXNG_DIR"
    # 优先使用内置 docker compose
    if docker compose version &> /dev/null; then
        docker compose up -d
    elif command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        print_error "Docker Compose 未安装"
        exit 1
    fi
    
    # 等待服务就绪
    print_info "等待 SearXNG 启动..."
    for i in {1..30}; do
        if curl -s "http://localhost:8080" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    print_success "SearXNG 已启动"
fi

# 3. 检查 Python 虚拟环境
print_header "准备 AI Agent"

cd "$CHATBOT_DIR"

if [ ! -d "venv" ]; then
    print_error "虚拟环境不存在"
    echo ""
    echo -e "${YELLOW}请先创建虚拟环境:${NC}"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# 4. 检查 .env 配置
if [ ! -f ".env" ]; then
    print_error ".env 文件不存在"
    echo ""
    echo -e "${YELLOW}请先配置 .env 文件:${NC}"
    echo "  cp .env.example .env"
    echo "  # 编辑 .env 添加 API keys"
    echo ""
    exit 1
fi

# 检查是否配置了至少一个 API key
if ! grep -q "^[A-Z]*_API_KEY=sk-" .env 2>/dev/null; then
    print_error "未检测到有效的 API key"
    echo ""
    echo -e "${YELLOW}请在 .env 中配置至少一个 LLM 提供商的 API key:${NC}"
    echo "  OPENAI_API_KEY=sk-..."
    echo "  或"
    echo "  DEEPSEEK_API_KEY=sk-..."
    echo "  或"
    echo "  ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    exit 1
fi

print_success "配置检查完成"

# 5. 显示启动信息
print_header "启动 AI Agent"

echo ""
echo -e "${GREEN}所有服务准备就绪！${NC}"
echo ""
echo -e "${BLUE}📍 服务地址:${NC}"
echo "   SearXNG: http://localhost:8080"
echo "   AI Agent: http://localhost:8000 (即将启动)"
echo ""
echo -e "${BLUE}💡 使用提示:${NC}"
echo "   1. 浏览器将自动打开 AI Agent 界面"
echo "   2. 输入 /search on 启用联网搜索"
echo "   3. 输入 /help 查看所有命令"
echo "   4. 按 Ctrl+C 停止服务"
echo ""
echo -e "${YELLOW}⏱️  正在启动 Chainlit...${NC}"
echo ""

# 6. 激活虚拟环境并启动 Chainlit
source venv/bin/activate

# 启动 Chainlit (带 watch 模式)
chainlit run app.py -w

# 脚本结束时的清理
echo ""
echo -e "${BLUE}AI Agent 已停止${NC}"
echo ""
echo -e "${YELLOW}💡 SearXNG 仍在后台运行${NC}"
echo "   停止 SearXNG: docker stop searxng"
echo "   查看状态: docker ps -f name=searxng"
echo ""

