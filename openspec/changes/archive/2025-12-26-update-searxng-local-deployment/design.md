# 设计文档: 本地 SearXNG 部署方案

## Context

当前系统依赖公共 SearXNG 实例 (https://searx.be),但在实际使用中发现:
- 公共实例经常出现连接超时和返回空结果
- 搜索质量和响应速度不稳定
- 无法保证长期可用性

用户反馈希望使用本地部署的 SearXNG 实例来获得稳定可靠的搜索服务。

## Goals / Non-Goals

**Goals:**
- 提供简单清晰的 SearXNG 本地部署指南
- 确保本地实例配置正确(JSON API、搜索格式等)
- 实现可靠的健康检查和配置验证机制
- 提供友好的错误提示和故障排查指导
- 保持代码简单,避免过度工程化

**Non-Goals:**
- 不提供 SearXNG 实例的自动部署和管理
- 不实现多实例负载均衡和故障转移
- 不对 SearXNG 内部实现进行定制修改
- 不提供搜索结果的缓存机制(保持简单)

## Decisions

### 1. 部署方式: Docker Compose
**决定:** 推荐使用 Docker Compose 在本地部署 SearXNG

**原因:**
- Docker Compose 是最简单的部署方式,适合个人用户
- SearXNG 官方提供了完善的 Docker 镜像和文档
- 可以快速启动和重启,方便调试和配置
- 不需要复杂的依赖管理和系统配置

**替代方案:**
- 直接 Docker 命令: 需要手动管理配置文件挂载,较复杂
- 源码安装: 需要 Python 环境和依赖,不适合非开发用户
- Kubernetes: 过于复杂,不适合个人场景

### 2. 配置验证策略
**决定:** 实现启动时健康检查 + 运行时降级

**原因:**
- 启动时检查可以及早发现配置问题
- 运行时降级确保基础对话功能不受影响
- 友好的错误提示帮助用户快速定位问题

**实现:**
```python
# 启动时检查
async def health_check() -> bool:
    """检查 SearXNG 服务是否可用"""
    try:
        response = await client.get(base_url)
        return response.status_code == 200
    except:
        return False

# 运行时降级
if search_enabled and search_service:
    try:
        results = await search_service.search(query)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        # 降级到无搜索模式,继续对话
```

### 3. 默认配置更新
**决定:** 默认 SEARXNG_URL 改为 `http://localhost:8080`

**原因:**
- 明确引导用户使用本地部署
- 本地部署是推荐的生产使用方式
- 避免用户误用不稳定的公共实例

**环境变量:**
```bash
# 默认本地部署地址
SEARXNG_URL=http://localhost:8080

# 可选:自定义端口
SEARXNG_URL=http://localhost:9090
```

### 4. 必要的 SearXNG 配置
**决定:** 明确要求以下配置项

**settings.yml 必要配置:**
```yaml
search:
  formats:
    - html
    - json  # 必须启用

server:
  secret_key: "your-secret-key"
  
general:
  instance_name: "Personal SearXNG"
  
# 启用 API
enable_api: true
```

**原因:**
- `json` 格式是系统集成的基础
- `enable_api: true` 确保 API 端点可用
- 其他配置可根据用户需求自定义

## Risks / Trade-offs

### Risk 1: 用户部署门槛
**风险:** 需要用户自行部署 Docker,可能增加使用难度

**缓解措施:**
- 提供详细的逐步部署指南
- 提供预配置的 docker-compose.yml 示例
- 在文档中提供常见问题排查步骤
- 在启动时提供清晰的错误提示和部署指引

### Risk 2: 本地实例维护成本
**风险:** 用户需要自行维护 SearXNG 实例

**缓解措施:**
- SearXNG 本身维护成本很低,通常无需干预
- 提供健康检查命令,方便用户诊断问题
- 文档中说明如何重启和更新实例

### Trade-off: 灵活性 vs 复杂度
**选择:** 优先保持简单,只支持单实例配置

**理由:**
- 个人用户场景下,单实例足够使用
- 避免引入复杂的负载均衡和故障转移逻辑
- 保持代码简洁易维护

## Migration Plan

### Phase 1: 准备阶段
1. 创建 SearXNG 部署文档
2. 准备 docker-compose.yml 模板
3. 更新 env.example 示例

### Phase 2: 代码更新
1. 更新默认配置为本地地址
2. 增强健康检查逻辑
3. 改进错误提示信息
4. 添加配置验证功能

### Phase 3: 文档完善
1. 更新 README.md 添加部署说明
2. 创建详细的部署指南文档
3. 添加故障排查章节
4. 更新快速开始文档

### Phase 4: 测试验证
1. 测试本地部署流程
2. 验证健康检查功能
3. 测试错误场景和降级机制
4. 确认文档准确性

### Rollback Plan
如果用户遇到部署问题:
1. 可临时使用公共实例(通过环境变量配置)
2. 或选择禁用搜索功能
3. 系统基础对话功能不受影响

## Open Questions

1. **Q: 是否需要提供备用的公共实例列表?**
   A: 不提供。公共实例质量不稳定,不建议用于生产。如果用户确实需要,可以自行在环境变量中配置。

2. **Q: 是否需要实现 SearXNG 配置的自动检查?**
   A: 实现基础的健康检查即可,不深入检查 settings.yml 配置。用户按照文档配置即可。

3. **Q: 是否支持其他搜索引擎(Google API, Bing API)?**
   A: 当前阶段不支持。SearXNG 已经聚合了多个搜索引擎,满足基本需求。

