# 全局引用管理器设计文档

## Context

在 Agent 模式下，AI 可能需要多次调用搜索工具来收集足够的信息回答用户问题。当前实现中，每次搜索的结果都独立编号（[1][2][3]...），这导致多次搜索的引用编号重复，用户无法清晰追踪信息来源。

## Goals / Non-Goals

### Goals
- ✅ 实现会话级别的全局引用管理
- ✅ 为所有搜索结果分配唯一的全局序号
- ✅ 在最终回答后展示完整的引用文章列表
- ✅ 保持与现有代码的兼容性
- ✅ 提升用户对信息来源的追溯能力

### Non-Goals
- ❌ 修改 Chat 模式的引用处理（保持独立编号）
- ❌ 跨会话的引用管理和持久化
- ❌ 引用去重和相似性检测
- ❌ 引用的重要性排序和推荐

## Decisions

### 决策 1: 会话级别的引用管理器

**选择**：在 Chainlit 会话状态中维护一个 GlobalCitationManager 实例

**理由**：
- 符合 Agent 单次对话的生命周期
- 简单清晰，无需复杂的状态同步
- 会话结束后自动清理，避免内存泄漏

**替代方案**：
1. **Agent 实例级别管理** - 但 Agent 可能被多次创建和销毁
2. **全局单例管理** - 需要处理并发和状态隔离，复杂度高

### 决策 2: 连续递增的全局编号

**选择**：为每次搜索结果分配连续的全局序号，从1开始递增

**算法**：
```python
# 第1次搜索：返回5个结果
results_1 = [1, 2, 3, 4, 5]

# 第2次搜索：返回3个结果
results_2 = [6, 7, 8]

# 第3次搜索：返回5个结果
results_3 = [9, 10, 11, 12, 13]
```

**理由**：
- 简单直观，用户容易理解
- 编号唯一，不会产生冲突
- 易于实现和维护

**替代方案**：
1. **分段编号** (如 1.1, 1.2, 2.1, 2.2) - 更复杂，用户理解成本高
2. **UUID** - 不直观，无法排序

### 决策 3: CitationProcessor 增强而非替换

**选择**：在现有 CitationProcessor 基础上添加 offset 参数，而非创建新类

**理由**：
- 复用现有的引用处理逻辑
- 保持 API 向后兼容
- 减少代码重复

**实现**：
```python
class CitationProcessor:
    def __init__(self, search_response: SearchResponse, offset: int = 0):
        """
        Args:
            search_response: 搜索结果
            offset: 编号偏移量（默认为0，从1开始）
        """
        self.offset = offset
        # 编号从 offset + 1 开始
```

### 决策 4: 引用列表展示位置和格式

**选择**：在 Agent 最终回答的末尾添加统一的引用列表

**格式**：
```markdown
[Agent 的最终回答内容]

---
**📚 引用文章列表:**

1. [文章标题1](URL1) - `域名1` - 来自: 第1次搜索
2. [文章标题2](URL2) - `域名2` - 来自: 第1次搜索
3. [文章标题3](URL3) - `域名3` - 来自: 第1次搜索
...
6. [文章标题6](URL6) - `域名6` - 来自: 第2次搜索
7. [文章标题7](URL7) - `域名7` - 来自: 第2次搜索
```

**理由**：
- 清晰分组，用户可以看到哪些来源来自哪次搜索
- 标准的学术引用格式
- 便于用户验证和追溯信息来源

**替代方案**：
1. **分散在各工具调用后** - 信息分散，用户需要滚动查看
2. **侧边栏显示** - 需要额外的 UI 组件，实现复杂

### 决策 5: 引用与搜索查询的关联

**选择**：在 GlobalCitationManager 中记录每个引用来源于哪次搜索查询

**数据结构**：
```python
class CitationEntry:
    number: int              # 全局编号
    url: str                # 来源URL
    title: str              # 文章标题
    domain: str             # 域名
    search_query: str       # 来源搜索查询
    search_round: int       # 第几次搜索
```

**理由**：
- 提供更多上下文信息
- 帮助用户理解 Agent 的搜索策略
- 便于调试和优化

## Risks / Trade-offs

### 风险 1: 引用编号过多导致列表冗长

**风险**：如果 Agent 进行了多次搜索（如5次），可能产生25个引用，列表会很长

**缓解措施**：
1. 只在引用列表中显示实际使用的引用（在回答中被引用的）
2. 提供折叠/展开功能
3. 限制 Agent 的最大搜索次数（默认5次）

### 风险 2: 性能影响

**风险**：维护全局引用映射和生成引用列表可能影响性能

**缓解措施**：
1. 使用字典结构，O(1) 查找
2. 延迟生成引用列表（仅在需要时）
3. 缓存已格式化的引用文本

### 权衡 1: 简单性 vs 灵活性

**选择简单性**：
- 固定的编号规则（连续递增）
- 固定的展示格式
- 不支持自定义编号规则

**理由**：
- 大多数场景下简单方案已足够
- 避免过度设计
- 易于理解和维护

### 权衡 2: 向后兼容 vs 代码简洁

**选择向后兼容**：
- CitationProcessor 保持现有 API
- 添加可选的 offset 参数
- Chat 模式完全不受影响

**理由**：
- 避免破坏现有功能
- 降低升级风险
- 渐进式改进

## Migration Plan

### 阶段 1: 实现核心功能（不破坏现有功能）
1. 实现 GlobalCitationManager 类
2. 增强 CitationProcessor 支持 offset
3. 单元测试验证

### 阶段 2: Agent 集成（仅影响 Agent 模式）
1. 在 ReActAgent 中集成 GlobalCitationManager
2. 修改 SearchTool 使用全局编号
3. 集成测试验证

### 阶段 3: UI 展示（用户可见变化）
1. 实现引用列表展示
2. 添加折叠/展开功能
3. 端到端测试

### 阶段 4: 文档和发布
1. 更新文档
2. 发布更新日志
3. 收集用户反馈

### 回滚计划
如果出现问题，可以：
1. 在 Agent 初始化时禁用 GlobalCitationManager
2. 回退到独立的 CitationProcessor（现有行为）
3. 无需数据迁移，因为是会话级别状态

## Open Questions

### Q1: 如何处理引用编号与 Markdown 列表的冲突？

**问题**：如果回答中包含 Markdown 编号列表，可能与引用编号冲突

**示例**：
```markdown
以下是三个要点：
[1] 第一个要点  <- 这是引用
[2] 第二个要点  <- 这是引用

另一个列表：
1. 列表项1     <- 这是 Markdown 列表
2. 列表项2
```

**解决方案**：
- 使用正则表达式精确匹配：`\[(\d+)\]`（方括号包裹的数字）
- Markdown 列表使用 `1.` 格式，不会冲突
- 如果用户在回答中手动写 [1]，会被识别为引用（这是预期行为）

### Q2: 是否需要引用去重？

**场景**：Agent 可能在不同搜索中获取到相同的文章

**当前决策**：不实现去重
- 保留所有引用，即使重复
- 用户可以看到 Agent 在不同上下文中多次找到同一来源
- 避免引用编号不连续的复杂性

**未来考虑**：
- 如果用户反馈引用重复是问题，可以添加去重逻辑
- 去重时合并来源信息（"来自: 第1次搜索, 第3次搜索"）

### Q3: 引用列表是否应该支持排序和过滤？

**当前决策**：按全局序号顺序展示，不支持排序过滤
- 简单直观
- 与回答中的引用编号对应

**未来考虑**：
- 按域名分组
- 按搜索轮次分组
- 仅显示被引用的来源

## 实现示例

### GlobalCitationManager 核心实现

```python
class GlobalCitationManager:
    """全局引用管理器，维护会话级别的引用列表"""
    
    def __init__(self):
        self.citations: List[CitationEntry] = []
        self.next_number = 1
        self.search_round = 0
    
    def add_search_results(
        self, 
        search_response: SearchResponse, 
        search_query: str
    ) -> tuple[int, int]:
        """
        添加搜索结果并分配全局编号
        
        Args:
            search_response: 搜索结果
            search_query: 搜索查询
            
        Returns:
            (start_number, end_number): 分配的编号范围
        """
        self.search_round += 1
        start_number = self.next_number
        
        for result in search_response.results:
            entry = CitationEntry(
                number=self.next_number,
                url=result.url,
                title=result.title,
                domain=self._extract_domain(result.url),
                search_query=search_query,
                search_round=self.search_round
            )
            self.citations.append(entry)
            self.next_number += 1
        
        end_number = self.next_number - 1
        return (start_number, end_number)
    
    def generate_citations_list(self, used_numbers: Set[int]) -> str:
        """
        生成引用列表
        
        Args:
            used_numbers: 回答中实际使用的引用编号
            
        Returns:
            格式化的引用列表 Markdown
        """
        if not used_numbers:
            return ""
        
        # 按搜索轮次分组
        by_round = {}
        for citation in self.citations:
            if citation.number in used_numbers:
                round_num = citation.search_round
                if round_num not in by_round:
                    by_round[round_num] = []
                by_round[round_num].append(citation)
        
        # 生成 Markdown
        lines = ["\n\n---", "**📚 引用文章列表:**\n"]
        
        for round_num in sorted(by_round.keys()):
            citations = by_round[round_num]
            lines.append(f"\n**第 {round_num} 次搜索** (查询: {citations[0].search_query})")
            for citation in sorted(citations, key=lambda c: c.number):
                lines.append(
                    f"{citation.number}. [{citation.title}]({citation.url}) "
                    f"- `{citation.domain}`"
                )
        
        return "\n".join(lines)
```

### Agent 集成示例

```python
class ReActAgent(BaseAgent):
    def __init__(self, llm, search_tool, config, citation_manager=None):
        self.citation_manager = citation_manager or GlobalCitationManager()
        # ... 其他初始化
    
    async def stream(self, user_input: str) -> AsyncIterator[AgentStep]:
        # 工具调用时传递引用管理器
        tool_results = []
        
        async for event in self.agent_executor.astream(stream_input):
            if "tools" in event:
                # 工具返回结果
                for msg in event["tools"]["messages"]:
                    tool_output = str(msg.content)
                    tool_results.append(tool_output)
                    
                    # 提取搜索结果并添加到全局引用
                    # (SearchTool 已使用全局编号格式化结果)
                    yield AgentStep(type="observation", content=tool_output)
        
        # 生成最终回答
        final_answer = await self._generate_final_answer(user_input, tool_results)
        
        # 提取使用的引用编号
        used_citations = self._extract_citation_numbers(final_answer)
        
        # 添加引用列表
        citations_list = self.citation_manager.generate_citations_list(used_citations)
        final_answer_with_citations = final_answer + citations_list
        
        yield AgentStep(type="final", content=final_answer_with_citations)
```

## 成功指标

1. **功能正确性**
   - ✅ 引用编号全局唯一，无重复
   - ✅ 引用列表包含所有搜索来源
   - ✅ 引用编号与实际来源匹配

2. **用户体验**
   - ✅ 引用列表清晰易读
   - ✅ 用户可以快速定位信息来源
   - ✅ 无性能问题（响应延迟 < 100ms）

3. **代码质量**
   - ✅ 单元测试覆盖率 > 80%
   - ✅ 集成测试通过
   - ✅ 向后兼容，Chat 模式不受影响

4. **文档完整性**
   - ✅ README 更新
   - ✅ API 文档更新
   - ✅ 用户指南更新

