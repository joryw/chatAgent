# Change: 迁移到本地部署的 SearXNG 实例

## Why

当前系统使用公共 SearXNG API (https://searx.be),存在以下问题:
1. 公共 API 不稳定,经常无法正常返回搜索结果
2. 受公共实例限流影响,无法保证服务质量
3. 依赖外部服务,存在可用性风险
4. 无法根据实际需求定制搜索配置

通过本地部署 SearXNG 实例,可以获得稳定可靠的搜索服务,完全掌控搜索质量和可用性。

## What Changes

- **BREAKING**: 要求用户本地部署 SearXNG 实例(通过 Docker)
- 更新 SearXNG 配置要求,确保启用 JSON API 和必要设置
- 增强搜索配置验证,确保本地实例正确配置
- 添加 SearXNG 部署指南和健康检查机制
- 更新环境变量配置,默认指向本地实例地址
- 改进错误提示,引导用户正确部署和配置

## Impact

**受影响的规范:**
- `specs/web-search/spec.md` - 更新 SearXNG 集成和配置要求

**受影响的代码:**
- `src/search/searxng_client.py` - 增强健康检查和配置验证
- `src/config/search_config.py` - 更新默认配置和验证逻辑
- `app.py` - 改进搜索服务初始化和错误提示
- `env.example` - 更新环境变量示例
- `README.md` - 添加 SearXNG 部署说明

**破坏性变更:**
- 用户需要自行部署 SearXNG 实例才能使用搜索功能
- 公共 API 不再作为默认选项推荐

