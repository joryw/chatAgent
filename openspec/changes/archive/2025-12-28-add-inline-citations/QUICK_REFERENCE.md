# 内联引用链接 - 快速参考

## 🎯 功能概述

将模型回答中的引用标记 `[1]`、`[2]` 转换为可点击的链接,用户可以直接跳转到来源网页。

## ✨ 核心特性

- **智能识别**: 自动识别 `[数字]` 格式的引用
- **一键跳转**: 点击引用直接打开来源网页
- **参考文献**: 自动生成完整的引用列表
- **实时处理**: 流式生成完成后瞬间转换

## 🚀 快速开始

### 1. 启动应用

```bash
# 激活虚拟环境并启动
cd /Users/jory/chatAgent
source venv/bin/activate
chainlit run app.py -w
```

应用现在运行在: **http://localhost:8001**

### 2. 启用搜索

在聊天界面:
- 点击设置图标 ⚙️
- 打开"联网搜索"开关 ✅

### 3. 测试功能

提问示例:
```
Python 是什么编程语言?
```

预期结果:
```
Python 是一种高级编程语言[[1]](https://python.org)...

---
📚 参考文献:
1. [Python Official](https://python.org) - `python.org`
```

## 📋 测试清单

- [ ] 引用链接显示为蓝色
- [ ] 点击链接能打开新页面
- [ ] 参考文献列表显示正确
- [ ] 多个引用都能正确转换
- [ ] 无效引用保持原样

## 🔧 技术实现

**核心类**: `CitationProcessor`
**位置**: `src/search/citation_processor.py`

**集成**: `app.py`
```python
citation_processor = CitationProcessor(search_response)
processed_response = citation_processor.process_response(full_response)
```

## 📚 完整文档

- [README.md](./README.md) - 功能详细介绍
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - 测试指南
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 实施总结
- [design.md](./design.md) - 技术设计
- [proposal.md](./proposal.md) - 功能提案

## ⚠️ 注意事项

1. **搜索必须启用**: 只在启用联网搜索时生效
2. **引用格式**: 仅支持 `[数字]` 格式
3. **编号范围**: 只转换有效的引用编号(在搜索结果范围内)
4. **SearXNG 依赖**: 需要 SearXNG 服务运行在 `localhost:8080`

## 🐛 故障排查

### 引用未转换?

检查:
1. 搜索是否启用
2. 是否执行了搜索(日志中查看)
3. 模型是否使用了引用标记

### 链接无法点击?

检查:
1. 浏览器控制台错误
2. Chainlit Markdown 渲染
3. URL 格式是否正确

## 📊 状态

✅ **已完成** - 核心功能已实现并测试
🚀 **已部署** - 应用运行在 http://localhost:8001

## 🎉 开始使用

访问: **http://localhost:8001**

体验全新的引用链接功能!

