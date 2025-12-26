# 文档迁移指南

> **创建时间：** 2025-12-26  
> **维护者：** chatAgent 团队

## 概述

本指南说明如何将现有文档迁移到新的文档管理体系中。

## 迁移映射

### 现有文档位置映射

| 现有文档 | 新位置 | 操作 |
|---------|--------|------|
| `docs/QUICK_START.md` | `docs/guides/quick-start/guide.md` | 已迁移 ✅ |
| `docs/CONFIGURATION.md` | `docs/guides/configuration/guide.md` | 已迁移 ✅ |
| `docs/STREAMING.md` | `docs/guides/streaming/guide.md` | 待迁移 |
| `PROJECT_OVERVIEW.md` | `docs/architecture/overview/doc.md` | 待迁移 |
| `IMPLEMENTATION_SUMMARY.md` | `docs/architecture/implementation/doc.md` | 待迁移 |
| `CONTRIBUTING.md` | `docs/development/contributing/guide.md` | 待迁移 |
| `USAGE_EXAMPLES.md` | `docs/features/*/examples.md` | 待迁移 |

## 迁移步骤

### 步骤1：备份现有文档

```bash
# 创建备份目录
mkdir -p docs/backup

# 备份现有文档
cp docs/*.md docs/backup/
cp *.md docs/backup/
```

### 步骤2：按分类迁移文档

#### 迁移指南类文档

```bash
# 示例：迁移 STREAMING.md
# 1. 创建目录
mkdir -p docs/guides/streaming

# 2. 复制并重命名
cp docs/STREAMING.md docs/guides/streaming/guide.md

# 3. 添加文档头部信息（手动编辑）
vim docs/guides/streaming/guide.md
```

#### 迁移架构文档

```bash
# 示例：迁移 PROJECT_OVERVIEW.md
mkdir -p docs/architecture/overview
cp PROJECT_OVERVIEW.md docs/architecture/overview/doc.md
```

#### 迁移开发文档

```bash
# 示例：迁移 CONTRIBUTING.md
mkdir -p docs/development/contributing
cp CONTRIBUTING.md docs/development/contributing/guide.md
```

### 步骤3：更新文档内容

对于每个迁移的文档，需要：

1. **添加文档头部信息**

```markdown
# [文档标题]

> **创建时间：** YYYY-MM-DD  
> **最后更新：** YYYY-MM-DD  
> **维护者：** [负责人]  
> **状态：** [状态]

## 概述

[简要说明]
```

2. **更新内部链接**

```markdown
# 旧链接
[配置说明](./CONFIGURATION.md)

# 新链接
[配置说明](../configuration/guide.md)
```

3. **添加相关文档链接**

```markdown
## 相关文档

- [快速入门](../quick-start/guide.md)
- [功能文档](../../features/model-invocation/doc.md)
```

### 步骤4：更新 README 索引

在 `docs/README.md` 中添加迁移后的文档链接。

### 步骤5：验证链接

```bash
# 安装链接检查工具
npm install -g markdown-link-check

# 检查所有文档链接
find docs -name "*.md" -exec markdown-link-check {} \;
```

## 迁移检查清单

### 迁移前

- [ ] 备份所有现有文档
- [ ] 创建新的目录结构
- [ ] 准备文档模板

### 迁移中

- [ ] 按分类复制文档到新位置
- [ ] 添加文档头部信息
- [ ] 更新内部链接
- [ ] 添加相关文档链接
- [ ] 统一使用中文

### 迁移后

- [ ] 验证所有链接有效
- [ ] 更新 README 索引
- [ ] 检查文档格式
- [ ] 提交变更到 Git
- [ ] 通知团队成员

## 批量迁移脚本

创建 `migrate_docs.sh` 脚本辅助迁移：

```bash
#!/bin/bash

# 文档迁移脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "开始文档迁移..."

# 创建备份
echo "${YELLOW}创建备份...${NC}"
mkdir -p docs/backup
cp docs/*.md docs/backup/ 2>/dev/null
cp *.md docs/backup/ 2>/dev/null
echo "${GREEN}✓ 备份完成${NC}"

# 迁移指南文档
echo "${YELLOW}迁移指南文档...${NC}"
[ -f "docs/STREAMING.md" ] && mkdir -p docs/guides/streaming && cp docs/STREAMING.md docs/guides/streaming/guide.md

# 迁移架构文档
echo "${YELLOW}迁移架构文档...${NC}"
[ -f "PROJECT_OVERVIEW.md" ] && mkdir -p docs/architecture/overview && cp PROJECT_OVERVIEW.md docs/architecture/overview/doc.md
[ -f "IMPLEMENTATION_SUMMARY.md" ] && mkdir -p docs/architecture/implementation && cp IMPLEMENTATION_SUMMARY.md docs/architecture/implementation/doc.md

# 迁移开发文档
echo "${YELLOW}迁移开发文档...${NC}"
[ -f "CONTRIBUTING.md" ] && mkdir -p docs/development/contributing && cp CONTRIBUTING.md docs/development/contributing/guide.md

echo "${GREEN}✓ 迁移完成${NC}"
echo ""
echo "后续步骤："
echo "1. 检查迁移的文档并添加头部信息"
echo "2. 更新文档内的链接"
echo "3. 更新 docs/README.md 索引"
echo "4. 运行 'git status' 查看变更"
```

使用方法：

```bash
# 赋予执行权限
chmod +x migrate_docs.sh

# 运行迁移脚本
./migrate_docs.sh
```

## 注意事项

### 1. 保留原文档

在确认新文档体系正常工作前，不要删除原文档：

```bash
# 暂时保留旧文档
mv docs/STREAMING.md docs/STREAMING.md.old
```

### 2. 更新外部引用

如果有外部链接引用旧文档位置：

1. 在 README.md 中更新链接
2. 如果有文档网站，更新网站配置
3. 通知团队成员使用新路径

### 3. Git 提交建议

```bash
# 分步提交，便于回滚

# 1. 提交新文档结构
git add docs/README.md docs/templates/
git commit -m "docs: add document management structure"

# 2. 提交迁移的文档
git add docs/guides/ docs/architecture/ docs/development/
git commit -m "docs: migrate existing documents to new structure"

# 3. 清理旧文档（确认无问题后）
git rm docs/STREAMING.md.old
git commit -m "docs: remove old document files"
```

## 迁移时间表

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 准备 | 备份、创建结构、准备模板 | 30分钟 |
| 迁移 | 复制文档、更新格式 | 2小时 |
| 验证 | 检查链接、格式验证 | 1小时 |
| 清理 | 删除旧文档、提交变更 | 30分钟 |
| **总计** | | **4小时** |

## 获取帮助

如果在迁移过程中遇到问题：

1. 查看 [文档管理规范](../openspec/project.md#文档管理规范)
2. 参考 [文档模板](./templates/)
3. 联系项目维护者

---

**最后更新：** 2025-12-26  
**维护者：** chatAgent 团队

