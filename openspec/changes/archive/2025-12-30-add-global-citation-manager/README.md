# 全局引用管理器提案

## 📋 提案概述

**变更ID**: `add-global-citation-manager`  
**状态**: ⏳ 待审批  
**创建时间**: 2025-12-30

## 🎯 问题描述

在 Agent 模式下，当 AI 需要多次搜索来收集信息时，存在以下问题：

### 当前行为示例

```
用户问题: "比较2024年最新的AI模型"

Agent 第1次搜索: "2024 AI models comparison"
结果: [1] GPT-4 Turbo, [2] Claude 3, [3] DeepSeek V2

Agent 第2次搜索: "latest AI benchmarks 2024"
结果: [1] MMLU scores, [2] HumanEval results, [3] Cost comparison
       ⚠️ 编号重复！与第1次搜索冲突

最终回答:
"根据最新信息 [1][2][3]，GPT-4 Turbo 表现最好..."
❌ 问题: 用户不知道 [1][2][3] 具体指哪些来源
```

### 核心问题

1. ❌ **引用编号重复** - 每次搜索都从 [1] 开始
2. ❌ **无法追踪来源** - 用户不知道引用来自哪次搜索
3. ❌ **引用列表分散** - 没有统一的引用文章列表

## ✨ 解决方案

实现**全局引用管理器 (GlobalCitationManager)**，为所有搜索结果分配唯一的全局序号。

### 期望行为示例

```
用户问题: "比较2024年最新的AI模型"

Agent 第1次搜索: "2024 AI models comparison"
结果: [1] GPT-4 Turbo, [2] Claude 3, [3] DeepSeek V2
      ✅ 全局编号 1-3

Agent 第2次搜索: "latest AI benchmarks 2024"
结果: [4] MMLU scores, [5] HumanEval results, [6] Cost comparison
      ✅ 全局编号 4-6，连续递增

最终回答:
"根据最新信息 [1][2][3][4][5]，GPT-4 Turbo 在 [4] 的基准测试中表现最好..."

---
📚 引用文章列表:

第 1 次搜索 (查询: 2024 AI models comparison)
1. [GPT-4 Turbo Released](https://openai.com/...) - `openai.com`
2. [Claude 3 Announcement](https://anthropic.com/...) - `anthropic.com`
3. [DeepSeek V2 Review](https://deepseek.com/...) - `deepseek.com`

第 2 次搜索 (查询: latest AI benchmarks 2024)
4. [MMLU Benchmark Results](https://huggingface.co/...) - `huggingface.co`
5. [HumanEval Scores 2024](https://github.com/...) - `github.com`
6. [AI Model Cost Analysis](https://techcrunch.com/...) - `techcrunch.com`
```

## 📦 核心功能

### 1. GlobalCitationManager 类

```python
class GlobalCitationManager:
    """会话级别的全局引用管理器"""
    
    def add_search_results(self, results, query) -> (start, end):
        """
        添加搜索结果并分配全局编号
        
        Returns:
            (start_number, end_number): 如 (1, 5) 或 (6, 10)
        """
    
    def generate_citations_list(self, used_numbers) -> str:
        """生成完整的引用文章列表"""
```

### 2. CitationProcessor 增强

```python
# 现有 API（Chat 模式）
processor = CitationProcessor(search_response)  # offset=0，从1开始

# 新 API（Agent 模式）
processor = CitationProcessor(search_response, offset=5)  # 从6开始
```

### 3. 引用编号分配规则

| 搜索轮次 | 结果数量 | 分配编号 | 下次起始编号 |
|---------|---------|---------|-------------|
| 第 1 次  | 5       | [1-5]   | 6           |
| 第 2 次  | 3       | [6-8]   | 9           |
| 第 3 次  | 5       | [9-13]  | 14          |
| ...     | ...     | ...     | ...         |

### 4. 引用列表展示

```markdown
---
**📚 引用文章列表:**

**第 1 次搜索** (查询: xxx)
1. [标题1](URL1) - `域名1`
2. [标题2](URL2) - `域名2`

**第 2 次搜索** (查询: yyy)
6. [标题6](URL6) - `域名6`
7. [标题7](URL7) - `域名7`
```

## 🔄 实现流程

### 阶段 1: 核心实现
- [ ] 实现 GlobalCitationManager 类
- [ ] 增强 CitationProcessor 支持 offset
- [ ] 单元测试

### 阶段 2: Agent 集成
- [ ] ReActAgent 集成全局引用管理器
- [ ] SearchTool 使用全局编号
- [ ] 集成测试

### 阶段 3: UI 展示
- [ ] 引用列表格式化
- [ ] 折叠/展开功能
- [ ] 端到端测试

### 阶段 4: 文档和发布
- [ ] 更新文档
- [ ] 发布更新日志

## 📊 影响范围

### 受影响的规范
- ✅ `agent-mode` - 添加全局引用管理需求
- ✅ `web-search` - 修改引用编号分配机制

### 受影响的代码
- `src/search/citation_processor.py` - 增强支持偏移量
- `src/agents/react_agent.py` - 集成全局引用管理器
- `src/agents/tools/search_tool.py` - 使用全局引用上下文
- `app.py` - 会话状态管理

### 向后兼容性
- ✅ **Chat 模式完全不受影响** - 仍使用独立编号
- ✅ **现有 API 保持兼容** - offset 参数可选
- ✅ **渐进式升级** - 可独立部署和测试

## 🎨 用户体验提升

### Before (当前)
```
Agent: "根据搜索结果 [1][2][3]..."
用户: 🤔 这些 [1][2][3] 具体是什么？哪次搜索的？
```

### After (改进后)
```
Agent: "根据搜索结果 [1][4][7]..."

📚 引用文章列表:
第 1 次搜索: 1, 2, 3
第 2 次搜索: 4, 5, 6
第 3 次搜索: 7, 8, 9

用户: ✅ 清晰！[1] 来自第1次搜索，[4] 来自第2次搜索
```

## 📈 成功指标

### 功能正确性
- ✅ 引用编号全局唯一，无重复
- ✅ 引用列表包含所有来源
- ✅ 引用编号与实际来源匹配

### 用户体验
- ✅ 引用列表清晰易读
- ✅ 快速定位信息来源
- ✅ 无性能问题（< 100ms）

### 代码质量
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试通过
- ✅ 向后兼容

## 📚 相关文档

- [完整提案](./proposal.md)
- [实现任务清单](./tasks.md)
- [技术设计文档](./design.md)
- [Agent Mode 规范变更](./specs/agent-mode/spec.md)
- [Web Search 规范变更](./specs/web-search/spec.md)

## ⚙️ 验证和审批

### 验证状态
```bash
✅ OpenSpec 验证通过
$ openspec validate add-global-citation-manager --strict
Change 'add-global-citation-manager' is valid
```

### 待审批事项
1. [ ] 产品经理审批 - 确认用户体验改进
2. [ ] 技术负责人审批 - 确认技术方案可行
3. [ ] 安全审查 - 确认无安全风险

## 🚀 下一步

1. **获得审批** - 等待相关人员审批提案
2. **开始实现** - 按照 tasks.md 中的清单逐步实现
3. **测试验证** - 确保功能正确性和性能
4. **文档更新** - 更新用户文档和开发文档
5. **发布上线** - 部署到生产环境

## 💡 常见问题

### Q1: 这会影响 Chat 模式吗？
**A**: 不会。Chat 模式完全不受影响，仍使用独立的引用编号（每次从1开始）。

### Q2: 引用编号会很大吗？
**A**: 取决于搜索次数。典型场景下（3-5次搜索），编号在1-25之间。

### Q3: 性能会受影响吗？
**A**: 不会。使用字典结构，查找是 O(1)，引用列表生成 < 100ms。

### Q4: 如何处理引用去重？
**A**: 当前版本不实现去重。保留所有引用，即使重复，用户可以看到 Agent 的搜索轨迹。

### Q5: 引用列表会很长吗？
**A**: 只显示实际使用的引用。如果回答只引用了 [1][5][9]，列表只包含这3条。

---

**创建者**: AI Assistant  
**创建时间**: 2025-12-30  
**最后更新**: 2025-12-30

