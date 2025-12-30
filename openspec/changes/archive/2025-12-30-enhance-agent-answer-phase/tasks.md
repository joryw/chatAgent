# 实施任务清单

## 1. 修改 answer_llm 为流式输出
- [x] 1.1 将 `_generate_answer_with_answer_llm` 方法从 `ainvoke` 改为 `astream`
- [x] 1.2 在流式输出中检测并提取 `reasoning_content`（DeepSeek-R1 等模型）
- [x] 1.3 通过 `AgentStep` 展示推理过程
- [x] 1.4 确保推理内容和回答内容分别展示

## 2. 实现引用标记实时转换
- [x] 2.1 创建引用标记检测和转换逻辑
- [x] 2.2 使用 CitationProcessor 处理引用转换
- [x] 2.3 从 GlobalCitationManager 获取对应的 URL
- [x] 2.4 将文本引用转换为 Markdown 链接格式 `[[数字]](URL)`
- [x] 2.5 处理边界情况（未找到引用、格式错误等）

## 3. 集成和测试
- [x] 3.1 在 `run_async` 方法中集成新的流式输出逻辑
- [x] 3.2 确保双 LLM 模式和单 LLM 模式都正常工作
- [x] 3.3 创建测试脚本验证引用转换功能
- [x] 3.4 验证引用链接格式（[[num]](url)）
- [x] 3.5 验证多轮搜索的引用编号正确性

## 4. 文档更新
- [x] 4.1 更新 OpenSpec 规范说明新的推理展示功能
- [x] 4.2 更新 OpenSpec 规范说明引用链接的交互方式

## 实施总结

### 已完成的功能

1. **流式输出与推理展示**
   - 创建了新的 `_generate_answer_with_answer_llm_streaming` 方法
   - 支持检测 DeepSeek-R1 等模型的 `reasoning_content`
   - 通过 `AgentStep` 类型为 "reasoning" 展示推理过程
   - 在 metadata 中标记推理类型（answer_phase）和模型来源

2. **引用链接转换**
   - 利用现有的 `CitationProcessor` 进行引用转换
   - 转换格式为 `[[num]](url)`，保持引用编号可见性
   - 在流式输出完成后添加引用列表
   - 支持多轮搜索的全局引用编号

3. **测试验证**
   - 创建了 `test_citation_conversion_simple.py` 测试脚本
   - 验证了单个引用、连续引用、两位数引用等场景
   - 验证了流式输出中的引用转换逻辑
   - 所有测试用例通过

### 技术实现细节

- **推理内容检测**: 检查 chunk 的 `additional_kwargs.reasoning_content`
- **流式输出**: 使用 `astream` 替代 `ainvoke`，实时yield AgentStep
- **引用格式**: 使用双括号格式 `[[num]](url)` 以保持编号可见性
- **向后兼容**: 保留了非流式的 fallback 方法

### 用户体验改进

1. 用户可以看到 answer_llm 的推理过程（特别是 DeepSeek-R1）
2. 引用标记自动转换为可点击的链接
3. 点击引用可直接跳转到来源，无需滚动到页面底部
4. 保持引用编号的可见性，便于对照

## 5. 引用链接功能修复（2025-12-30）

### 问题
- 引用标记 [1]、[2] 不能点击
- 流式输出时只输出了原始格式，没有转换为 Markdown 链接

### 修复措施
- [x] 5.1 在流式输出完成后添加引用转换逻辑
- [x] 5.2 创建新的步骤类型 `citation_update` 用于替换 UI 内容
- [x] 5.3 在 `app.py` 中添加 `citation_update` 步骤处理
- [x] 5.4 修复错误恢复路径中的引用转换逻辑
- [x] 5.5 测试验证引用链接可点击

### 修改文件
- `src/agents/react_agent.py` - 添加引用转换和 citation_update 步骤
- `app.py` - 添加 citation_update 处理逻辑

### 文档
- `CITATION_LINKS_FIX.md` - 详细的修复说明和测试步骤

