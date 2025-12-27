#!/bin/bash
# SearXNG 部署验证脚本
# 用于验证 SearXNG 是否正确部署和配置

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 SearXNG 部署验证工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

# 测试函数
test_step() {
    local description="$1"
    local command="$2"
    
    echo -n "📋 $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAILED++))
        return 1
    fi
}

# 可选测试 (失败不计入总数)
test_optional() {
    local description="$1"
    local command="$2"
    
    echo -n "📋 $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  可选项未通过${NC}"
        return 1
    fi
}

# 详细测试 (显示输出)
test_detailed() {
    local description="$1"
    local command="$2"
    
    echo "📋 $description..."
    
    if output=$(eval "$command" 2>&1); then
        echo -e "${GREEN}✅ 通过${NC}"
        echo "$output" | head -5
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        echo "$output"
        ((FAILED++))
        return 1
    fi
}

echo "━━━ 1. 前置检查 ━━━"
echo ""

test_step "Docker 已安装" "command -v docker"
test_step "Docker Compose 已安装" "command -v docker compose"
test_step "Docker 服务运行中" "docker info"

echo ""
echo "━━━ 2. 容器状态检查 ━━━"
echo ""

if docker ps | grep -q searxng; then
    echo -e "${GREEN}✅ SearXNG 容器正在运行${NC}"
    ((PASSED++))
    
    # 显示容器信息
    echo ""
    echo "容器信息:"
    docker ps | grep searxng | awk '{print "  ID: "$1"\n  状态: "$5"\n  端口: "$11}'
    echo ""
else
    echo -e "${RED}❌ SearXNG 容器未运行${NC}"
    ((FAILED++))
    echo ""
    echo "💡 提示: 运行 'docker compose up -d' 启动容器"
    echo ""
    exit 1
fi

test_step "容器健康状态正常" "docker inspect searxng | grep -q '\"Status\": \"running\"'"

echo ""
echo "━━━ 3. 网络连接检查 ━━━"
echo ""

test_step "端口 8080 监听中" "lsof -i :8080 || netstat -an | grep -q 8080"
test_step "Web 界面可访问" "curl -sf http://localhost:8080"
test_step "HTTP 状态码正常" "curl -sf -o /dev/null -w '%{http_code}' http://localhost:8080 | grep -q 200"

echo ""
echo "━━━ 4. JSON API 检查 (最重要) ━━━"
echo ""

# JSON API 详细测试
echo "📋 测试 JSON API 响应..."
JSON_RESPONSE=$(curl -sf "http://localhost:8080/search?q=test&format=json" 2>&1)

if echo "$JSON_RESPONSE" | jq . > /dev/null 2>&1; then
    echo -e "${GREEN}✅ JSON API 工作正常${NC}"
    ((PASSED++))
    
    # 解析 JSON 响应
    QUERY=$(echo "$JSON_RESPONSE" | jq -r '.query' 2>/dev/null || echo "N/A")
    RESULTS_COUNT=$(echo "$JSON_RESPONSE" | jq '.results | length' 2>/dev/null || echo "0")
    
    echo ""
    echo "  查询: $QUERY"
    echo "  结果数: $RESULTS_COUNT"
    
    if [ "$RESULTS_COUNT" -gt 0 ]; then
        echo ""
        echo "  前 3 条结果:"
        echo "$JSON_RESPONSE" | jq -r '.results[0:3] | .[] | "    • " + .title' 2>/dev/null || true
    fi
    echo ""
else
    echo -e "${RED}❌ JSON API 失败${NC}"
    ((FAILED++))
    echo ""
    echo "响应内容:"
    echo "$JSON_RESPONSE" | head -10
    echo ""
fi

test_step "JSON 响应包含 query 字段" "curl -sf 'http://localhost:8080/search?q=test&format=json' | jq -e '.query'"
test_step "JSON 响应包含 results 数组" "curl -sf 'http://localhost:8080/search?q=test&format=json' | jq -e '.results | length'"

echo ""
echo "━━━ 5. 配置文件检查 ━━━"
echo ""

if [ -f "searxng/settings.yml" ] || [ -f "../searxng/settings.yml" ]; then
    SETTINGS_FILE="searxng/settings.yml"
    [ -f "../searxng/settings.yml" ] && SETTINGS_FILE="../searxng/settings.yml"
    
    echo -e "${GREEN}✅ settings.yml 文件存在${NC}"
    ((PASSED++))
    
    # 检查关键配置
    echo ""
    echo "📋 检查关键配置..."
    
    if grep -q "json" "$SETTINGS_FILE"; then
        echo -e "  JSON 格式: ${GREEN}✅ 已启用${NC}"
        ((PASSED++))
    else
        echo -e "  JSON 格式: ${RED}❌ 未启用${NC}"
        ((FAILED++))
        echo ""
        echo "  ⚠️  请在 settings.yml 中添加:"
        echo "  search:"
        echo "    formats:"
        echo "      - html"
        echo "      - json"
        echo ""
    fi
    
    # 检查搜索引擎配置
    ENGINES_COUNT=$(grep -c "engine:" "$SETTINGS_FILE" 2>/dev/null || echo "0")
    echo "  配置的搜索引擎: $ENGINES_COUNT 个"
    
else
    echo -e "${RED}❌ settings.yml 文件不存在${NC}"
    ((FAILED++))
    echo ""
    echo "💡 提示: 请创建 searxng/settings.yml 配置文件"
    echo ""
fi

echo ""
echo "━━━ 6. 搜索功能测试 ━━━"
echo ""

# 测试多个搜索关键词
test_keywords=("python" "docker" "searxng")

for keyword in "${test_keywords[@]}"; do
    test_optional "搜索关键词: $keyword" "curl -sf 'http://localhost:8080/search?q=$keyword&format=json' | jq -e '.results | length > 0'"
done

echo ""
echo "━━━ 7. 性能检查 ━━━"
echo ""

# 测试响应时间
echo "📋 测试响应时间..."
START_TIME=$(date +%s.%N)
curl -sf "http://localhost:8080/search?q=test&format=json" > /dev/null
END_TIME=$(date +%s.%N)
RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc)

echo "  响应时间: ${RESPONSE_TIME}s"

if (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
    echo -e "  ${GREEN}✅ 响应时间正常 (< 5s)${NC}"
    ((PASSED++))
else
    echo -e "  ${YELLOW}⚠️  响应时间较慢 (> 5s)${NC}"
    echo "  💡 考虑优化配置或增加资源"
fi

# 检查资源使用
echo ""
echo "📋 容器资源使用:"
docker stats --no-stream searxng | tail -1 | awk '{print "  CPU: "$3"\n  内存: "$7}'

echo ""
echo "━━━ 8. 环境变量检查 ━━━"
echo ""

if [ -f ".env" ] || [ -f "../.env" ]; then
    ENV_FILE=".env"
    [ -f "../.env" ] && ENV_FILE="../.env"
    
    echo -e "${GREEN}✅ .env 文件存在${NC}"
    ((PASSED++))
    
    SEARXNG_URL=$(grep "SEARXNG_URL" "$ENV_FILE" 2>/dev/null | cut -d= -f2 || echo "未设置")
    echo "  SEARXNG_URL: $SEARXNG_URL"
    
    if [ "$SEARXNG_URL" = "http://localhost:8080" ]; then
        echo -e "  ${GREEN}✅ URL 配置正确${NC}"
        ((PASSED++))
    else
        echo -e "  ${YELLOW}⚠️  URL 可能需要调整${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .env 文件不存在 (可选)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 验证结果汇总"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL=$((PASSED + FAILED))
SUCCESS_RATE=0

if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; $PASSED * 100 / $TOTAL" | bc)
fi

echo "  通过: ${GREEN}$PASSED${NC}"
echo "  失败: ${RED}$FAILED${NC}"
echo "  成功率: ${SUCCESS_RATE}%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 恭喜! SearXNG 部署完全正确!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "✅ 您现在可以在 AI 助手中使用联网搜索功能了!"
    echo ""
    echo "📝 下一步:"
    echo "  1. 在 .env 文件中设置: SEARXNG_URL=http://localhost:8080"
    echo "  2. 重启 AI 助手"
    echo "  3. 在聊天界面输入: /search on"
    echo "  4. 开始提问需要联网搜索的问题"
    echo ""
    exit 0
elif [ $FAILED -le 3 ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  SearXNG 基本可用,但有些问题需要修复${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "💡 建议:"
    echo "  1. 查看上面标记为 ❌ 的项目"
    echo "  2. 参考故障排查文档: docs/guides/troubleshooting/searxng.md"
    echo "  3. 检查日志: docker compose logs searxng"
    echo ""
    exit 1
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ SearXNG 部署存在严重问题${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "🔧 故障排查步骤:"
    echo "  1. 查看详细日志: docker compose logs searxng"
    echo "  2. 检查配置文件: cat searxng/settings.yml"
    echo "  3. 验证端口: lsof -i :8080"
    echo "  4. 阅读故障排查文档: docs/guides/troubleshooting/searxng.md"
    echo ""
    echo "需要帮助? 提交 Issue 时请附上本验证结果"
    echo ""
    exit 1
fi

