# 联网搜索功能完整打通提案

本提案旨在解决当前联网搜索功能使用公共 API 不稳定的问题,通过本地部署 SearXNG 实例实现稳定可靠的搜索服务。

## 📋 提案概览

**变更ID:** `update-searxng-local-deployment`  
**类型:** 功能改进 (Breaking Change)  
**状态:** 待审批  
**受影响规范:** `web-search`

## 🎯 核心目标

将搜索功能从依赖公共 SearXNG API 迁移到本地部署的 SearXNG 实例,解决以下问题:

1. ❌ **公共 API 不稳定** - 经常无法正常返回结果
2. ❌ **服务质量无保障** - 受限流影响,响应慢
3. ❌ **依赖外部服务** - 存在可用性风险
4. ✅ **完全掌控** - 本地部署,稳定可靠

## 📚 文档结构

```
openspec/changes/update-searxng-local-deployment/
├── README.md           # 本文件 - 提案总览
├── proposal.md         # 详细提案 - 为什么改、改什么、影响范围
├── design.md           # 设计文档 - 技术决策和实施方案
├── tasks.md            # 任务清单 - 具体实施步骤
└── specs/
    └── web-search/
        └── spec.md     # 规范变更 - MODIFIED/ADDED 需求
```

## 🔑 关键变更

### 1. 部署方式改变 (Breaking Change)

**之前:**
```bash
# 使用公共实例 (默认)
SEARXNG_URL=https://searx.be
```

**之后:**
```bash
# 使用本地部署实例 (推荐)
SEARXNG_URL=http://localhost:8080
```

### 2. SearXNG 本地部署

**推荐方案:** Docker Compose

**部署步骤:**
```bash
# 1. 创建 docker-compose.yml
services:
  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng
    restart: unless-stopped

# 2. 配置 settings.yml
search:
  formats:
    - html
    - json  # 必须启用

# 启用 API
enable_api: true

# 3. 启动服务
docker-compose up -d
```

### 3. 增强功能

#### 配置验证
- ✅ 启动时检查 SearXNG 服务可用性
- ✅ 验证 JSON API 是否正确配置
- ✅ 提供明确的配置错误提示

#### 健康检查
- ✅ 实时监控服务状态
- ✅ 失败时自动降级
- ✅ 保证基础对话不受影响

#### 文档完善
- ✅ 详细的部署指南
- ✅ 配置模板文件
- ✅ 故障排查文档
- ✅ 快速开始指引

## 📖 快速查看

### 查看提案详情
```bash
# 显示完整提案
openspec show update-searxng-local-deployment

# 查看规范变更
openspec show update-searxng-local-deployment --json --deltas-only
```

### 验证提案
```bash
# 严格验证
openspec validate update-searxng-local-deployment --strict
```

## 📝 实施步骤 (7个阶段)

根据 `tasks.md`,实施分为以下阶段:

1. **SearXNG 部署文档** - 创建详细部署指南
2. **配置更新** - 更新默认配置和环境变量
3. **健康检查增强** - 实现配置验证和服务检查
4. **初始化流程改进** - 优化启动流程和错误提示
5. **文档更新** - 完善用户文档和故障排查
6. **测试验证** - 端到端测试和场景验证
7. **规范更新** - 应用 spec delta 到主规范

详细任务清单请查看 `tasks.md`。

## 🎨 设计决策

详细技术决策请查看 `design.md`,关键决策包括:

### 1. 部署方式: Docker Compose
- ✅ 最简单的个人部署方式
- ✅ 官方支持,文档完善
- ✅ 快速启动,易于调试

### 2. 配置验证策略
- 启动时健康检查 + 运行时降级
- 友好的错误提示和修复建议
- 保证基础功能不受影响

### 3. 默认配置
- 默认本地地址: `http://localhost:8080`
- 明确引导用户使用本地部署
- 避免误用不稳定的公共实例

## 📊 影响范围

### 代码文件
- `src/search/searxng_client.py` - 健康检查和验证
- `src/config/search_config.py` - 默认配置更新
- `app.py` - 初始化逻辑改进
- `env.example` - 环境变量示例
- `README.md` - 部署说明

### 文档文件
- `docs/guides/searxng-deployment.md` (新建)
- `docs/guides/quick-start/README.md` (更新)
- `docs/guides/troubleshooting/searxng.md` (新建)

### 配置文件
- `docker-compose.yml` (模板)
- `settings.yml` (模板)

## ⚠️ 注意事项

### 破坏性变更
- 用户必须自行部署 SearXNG 才能使用搜索功能
- 现有使用公共 API 的配置需要更新
- 需要 Docker 环境支持

### 迁移指导
1. 按照新文档部署本地 SearXNG
2. 更新环境变量配置
3. 重启应用并验证搜索功能

### 回退方案
如遇部署问题,可以:
- 临时使用公共实例 (修改环境变量)
- 禁用搜索功能 (基础对话不受影响)

## ✅ 验收标准

### 功能验收
- [ ] 用户可按文档成功部署 SearXNG
- [ ] 启动时正确验证配置
- [ ] 搜索功能正常返回结果
- [ ] 失败时正确降级
- [ ] 错误提示清晰有用

### 文档验收
- [ ] 部署文档完整可执行
- [ ] 配置示例准确可用
- [ ] 故障排查覆盖常见问题
- [ ] README 有明确指引

### 代码质量
- [ ] 遵循项目规范
- [ ] 日志清晰有用
- [ ] 错误处理健全
- [ ] 无遗留公共 API 引用

## 🚀 下一步

1. **审批阶段** - 等待审批通过
2. **实施阶段** - 按 tasks.md 逐步实施
3. **测试验证** - 完整功能和文档测试
4. **归档阶段** - 部署后归档到 archive/

## 📞 相关资源

- [SearXNG 官方文档](https://docs.searxng.org/)
- [Docker 安装指南](https://docs.docker.com/get-docker/)
- [项目 OpenSpec 规范](../../project.md)

---

**创建时间:** 2025-12-26  
**创建者:** AI Assistant  
**审批状态:** 待审批

