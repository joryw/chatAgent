# Bug 修复：Agent 递归限制错误显示问题

## 问题描述

**症状**：当 Agent 达到最大迭代次数限制时，即使成功生成了答案并显示了引用，界面仍然会显示错误消息：
```
Sorry, need more steps to process this request.
```

**影响**：用户体验不佳，看起来像是 Agent 失败了，但实际上已经成功生成了答案。

## 根本原因

当 LangGraph Agent 达到 `recursion_limit`（最大迭代次数）时：

1. LangGraph 抛出递归限制异常
2. 我们的代码捕获异常并正确生成了答案
3. **但是** 在 yield 最终答案后，代码没有 `return`
4. 继续执行异常处理的其他分支
5. 最终 yield 了一个 `type="error"` 的步骤

## 修复方案

在所有处理递归限制异常并生成答案的代码路径后，添加明确的 `return` 语句：

### 修复位置（共 4 处）

#### 1. 双 LLM 模式 - 流式答案生成后
```python
# After streaming is complete, process citations and add reference list
if self.citation_manager and tool_results:
    # ... 处理引用列表 ...
    yield AgentStep(
        type="final",
        content=citations_list,
    )

# Successfully generated answer, exit exception handler
return  # ✅ 新增
```

**位置**：`src/agents/react_agent.py` 第 1032 行附近

#### 2. 单 LLM 模式 - 生成答案后
```python
answer = await self._generate_answer_with_answer_llm(
    user_input, tool_results, tool_calls
)
yield AgentStep(
    type="final",
    content=answer,
)

# Successfully generated answer, exit exception handler
return  # ✅ 新增
```

**位置**：`src/agents/react_agent.py` 第 1061 行附近

#### 3. 回退方法 - 成功执行后
```python
result = await self.run(user_input)
for step in result.steps:
    yield step
yield AgentStep(
    type="final",
    content=result.final_answer,
)
# Successfully generated answer using fallback, exit exception handler
return  # ✅ 新增
```

**位置**：`src/agents/react_agent.py` 第 1078 行附近

#### 4. 嵌套递归限制 - 回退方法也遇到限制时
```python
if "recursion_limit" in str(fallback_error).lower() and tool_results:
    logger.warning("回退方法也达到递归限制，使用已收集的结果生成答案")
    answer = await self._generate_answer_with_answer_llm(
        user_input, tool_results, tool_calls
    )
    yield AgentStep(
        type="final",
        content=answer,
    )
    # Successfully generated answer, exit exception handler
    return  # ✅ 新增
```

**位置**：`src/agents/react_agent.py` 第 1090 行附近

## 验证

修复后的行为：
1. ✅ Agent 执行多次搜索（例如 4 次）
2. ✅ 达到递归限制时，捕获异常
3. ✅ 基于已收集的工具结果生成答案
4. ✅ 显示最终答案和引用列表
5. ✅ **不再显示错误消息**
6. ✅ 用户看到完整、正确的答案

## 测试场景

### 场景 1：Agent 达到迭代限制但有搜索结果
```
用户问题：搜索下github热门榜的热门项目

预期行为：
- Agent 执行 3-4 次搜索
- 收集搜索结果 [1-12]
- 达到最大迭代次数
- 生成基于搜索结果的答案
- 显示全局引用列表
- ❌ 不显示 "Sorry, need more steps" 错误
```

### 场景 2：Agent 达到迭代限制但无搜索结果
```
预期行为：
- Agent 尝试多次操作
- 达到最大迭代次数
- 基于模型知识直接回答
- ❌ 不显示错误消息
```

## 相关文件

- `src/agents/react_agent.py` - Agent 执行逻辑
- `CHANGELOG.md` - 变更日志
- `tests/test_agent_recursion_limit_fix.py` - 测试文档

## 时间线

- **2025-12-30**：发现并修复 bug
- **修复内容**：4 个明确的 `return` 语句
- **影响范围**：所有达到迭代限制的 Agent 执行

## 受益

- ✅ **清晰的用户体验**：只显示答案，不显示错误
- ✅ **正确的错误恢复**：达到限制时优雅地生成答案
- ✅ **一致的行为**：所有代码路径都正确处理
- ✅ **减少困惑**：用户不会看到误导性的错误消息

