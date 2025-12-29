# 技术设计: 内联引用链接

## Context

当前系统已经支持联网搜索功能,模型会在回答中使用 [1]、[2] 等标记来引用搜索结果。但这些标记只是纯文本,用户无法直接点击跳转到来源。

**现有实现**:
- 搜索结果在 prompt 中传递给模型(包含 URL)
- 模型生成包含引用标记的回答
- 搜索来源在回答后单独显示(已支持 Markdown 链接)

**核心挑战**:
1. 如何在流式生成过程中识别和转换引用标记
2. 如何维护引用编号和 URL 的映射关系
3. 如何保证转换的准确性(避免误转换)

## Goals / Non-Goals

**Goals**:
- ✅ 将回答中的 [1]、[2] 等引用标记转换为可点击链接
- ✅ 支持流式生成时的实时转换
- ✅ 在回答末尾添加完整的引用列表
- ✅ 保持原有的搜索来源显示功能

**Non-Goals**:
- ❌ 不处理复杂的引用格式(如 [1,2,3] 或 [1-3])
- ❌ 不改变模型的引用行为(仍使用 [数字] 格式)
- ❌ 不支持自定义引用样式

## Decisions

### Decision 1: 使用正则表达式解析引用标记

**What**: 使用正则表达式识别回答中的 `[数字]` 模式

**Why**:
- 简单高效,易于维护
- 可以精确匹配数字引用
- 支持流式处理(逐字符或逐词处理)

**Pattern**: `\[(\d+)\]` - 匹配方括号中的数字

**Example**:
```python
import re

def find_citations(text: str) -> List[int]:
    """Find all citation numbers in text."""
    pattern = r'\[(\d+)\]'
    matches = re.finditer(pattern, text)
    return [int(match.group(1)) for match in matches]
```

### Decision 2: 回答生成完成后统一转换引用

**What**: 在流式生成完成后,对完整回答进行一次性引用转换

**Why**:
- 避免流式过程中的部分匹配问题(如 "[ 1]" 还未完成)
- 确保转换的准确性和完整性
- 实现简单,易于测试

**Alternatives considered**:
- 流式过程中实时转换 → 复杂度高,可能出现误转换
- 使用 LLM 后处理 → 成本高,速度慢

### Decision 3: 使用 Markdown 链接格式

**What**: 将 `[1]` 转换为 `[[1]](url)` 格式

**Why**:
- Chainlit 原生支持 Markdown 渲染
- 保留引用标记的视觉呈现 [1]
- 用户可以点击跳转

**Example**:
```markdown
根据搜索结果[1]，Python是一种高级编程语言[2]。

转换后:
根据搜索结果[[1]](https://example.com/python)，
Python是一种高级编程语言[[2]](https://python.org)。
```

### Decision 4: 在回答末尾添加引用列表

**What**: 在转换后的回答末尾添加"参考文献"部分

**Why**:
- 提供完整的来源信息
- 方便用户查看所有引用
- 符合学术引用习惯

**Format**:
```markdown
---
**📚 参考文献:**
1. [Python Programming](https://example.com/python) - example.com
2. [Python.org](https://python.org) - python.org
```

## Implementation Details

### Core Classes

#### CitationProcessor
```python
class CitationProcessor:
    """Process and convert citations in model responses."""
    
    def __init__(self, search_response: SearchResponse):
        """Initialize with search results.
        
        Args:
            search_response: SearchResponse containing URLs for citations
        """
        self.search_response = search_response
        self._build_citation_map()
    
    def _build_citation_map(self) -> None:
        """Build mapping from citation number to URL."""
        self.citation_map = {}
        for idx, result in enumerate(self.search_response.results, 1):
            self.citation_map[idx] = {
                'url': result.url,
                'title': result.title,
                'domain': self._extract_domain(result.url)
            }
    
    def convert_citations(self, text: str) -> str:
        """Convert [num] to [[num]](url) format.
        
        Args:
            text: Original text with citations
        
        Returns:
            Text with clickable citation links
        """
        def replace_citation(match):
            num = int(match.group(1))
            if num in self.citation_map:
                url = self.citation_map[num]['url']
                return f"[[{num}]]({url})"
            return match.group(0)  # Keep original if not found
        
        pattern = r'\[(\d+)\]'
        return re.sub(pattern, replace_citation, text)
    
    def get_citations_list(self, text: str) -> str:
        """Generate formatted citations list.
        
        Args:
            text: Text to extract citations from
        
        Returns:
            Formatted citations section
        """
        cited_nums = self._extract_citations(text)
        if not cited_nums:
            return ""
        
        citations = "\n\n---\n**📚 参考文献:**\n"
        for num in sorted(cited_nums):
            if num in self.citation_map:
                info = self.citation_map[num]
                citations += f"\n{num}. [{info['title']}]({info['url']}) - `{info['domain']}`"
        
        return citations
```

### Integration Flow

```
用户提问 + 搜索启用
  ↓
执行搜索 → 获取 SearchResponse
  ↓
创建 CitationProcessor(search_response)
  ↓
模型流式生成回答(包含 [1], [2] 等)
  ↓
回答生成完成
  ↓
processor.convert_citations(response_text)
  ↓
processor.get_citations_list(response_text)
  ↓
display: converted_text + citations_list
```

### Code Changes

**app.py** (主要修改):
```python
# After streaming completes
if search_response and not search_response.is_empty():
    # Convert citations to clickable links
    processor = CitationProcessor(search_response)
    full_response = processor.convert_citations(full_response)
    citations_list = processor.get_citations_list(full_response)
    
    # Update message with converted text
    response_msg.content = full_response + citations_list
    await response_msg.update()
```

## Risks / Trade-offs

### Risk 1: 误转换非引用的数字

**Risk**: 回答中的 [10] 可能是列表项,不是引用

**Mitigation**:
- 只转换有效的引用编号(在 search_response 范围内)
- 保留原文如果编号超出范围
- 在 prompt 中明确引用格式要求

### Risk 2: Markdown 渲染问题

**Risk**: Chainlit 可能不正确渲染嵌套的方括号

**Mitigation**:
- 测试不同的引用格式
- 必要时使用 HTML 链接: `<a href="url">[1]</a>`
- 提供降级方案(保持原有的独立来源显示)

### Trade-off: 实时转换 vs 完成后转换

**选择**: 完成后转换

**Pros**:
- 实现简单可靠
- 避免流式过程中的部分匹配问题
- 性能开销小(一次性处理)

**Cons**:
- 用户需要等回答完成才能看到链接
- 无法在生成过程中点击引用

**Justification**: 对于大多数场景,回答生成速度很快,等待完成是可接受的。简单性和可靠性更重要。

## Open Questions

- ❓ 是否需要高亮显示引用链接(如特殊颜色)?
  - 答案: 使用 Chainlit 默认链接样式即可
  
- ❓ 如果模型引用了不存在的编号怎么办?
  - 答案: 保留原文,不转换。在日志中记录警告
  
- ❓ 是否需要显示引用的使用频率?
  - 答案: 不需要,保持简单

