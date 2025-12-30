## MODIFIED Requirements

### Requirement: 分阶段模型使用
系统必须（SHALL）在 Agent 执行的不同阶段使用相应的 LLM 模型，确保工具调用阶段使用 function_call_llm，回答生成阶段使用 answer_llm。

#### Scenario: 工具调用阶段使用 function_call_llm
- **WHEN** Agent 开始处理用户问题
- **THEN** 系统使用 function_call_llm 进行推理和工具调用决策
- **AND** 所有工具调用相关的 LLM 调用都使用 function_call_llm
- **AND** 在 UI 中标识当前使用的是工具调用模型

#### Scenario: 回答生成阶段使用 answer_llm
- **WHEN** Agent 完成工具调用循环并准备生成最终回答
- **THEN** 系统切换到 answer_llm
- **AND** 使用 answer_llm 基于工具调用结果生成最终回答
- **AND** 在 UI 中标识当前使用的是回答生成模型
- **AND** 使用流式输出（astream）而非非流式输出（ainvoke）生成最终回答
- **AND** 最终回答以流式方式实时展示在 UI 中

#### Scenario: 模型切换提示
- **WHEN** Agent 从工具调用阶段切换到回答生成阶段
- **THEN** 系统在 UI 中显示模型切换提示
- **AND** 说明切换的原因（工具调用结果已满足要求）
- **AND** 展示使用的模型信息

#### Scenario: 流式输出支持
- **WHEN** Agent 使用双模型执行任务
- **THEN** 工具调用阶段的流式输出使用 function_call_llm
- **AND** 回答生成阶段的流式输出使用 answer_llm
- **AND** 两个阶段的流式输出无缝衔接
- **AND** 回答生成阶段必须使用流式输出，不允许使用非流式输出

## ADDED Requirements

### Requirement: 回答阶段推理展示
系统必须（SHALL）在 Agent 回答生成阶段展示 answer_llm 的推理过程，特别是对于支持推理的模型（如 DeepSeek-R1），让用户了解模型如何组织和生成最终回答。

#### Scenario: 检测推理内容
- **WHEN** answer_llm 使用流式输出生成回答
- **THEN** 系统检测流式响应中的 `reasoning_content` 字段
- **AND** 系统检测流式响应中的常规 `content` 字段
- **AND** 区分推理内容和回答内容

#### Scenario: 展示推理过程
- **WHEN** answer_llm 生成推理内容
- **THEN** 在 UI 中创建 "思考回答方式..." Step
- **AND** 流式展示推理内容
- **AND** 标识这是 answer_llm 的推理过程
- **AND** 推理完成后自动折叠 Step

#### Scenario: 展示最终回答
- **WHEN** answer_llm 生成回答内容
- **THEN** 在 UI 中流式展示回答内容
- **AND** 回答内容与推理内容分开展示
- **AND** 保持流式输出的实时性

#### Scenario: 无推理内容的情况
- **WHEN** answer_llm 不提供推理内容（如 GPT-4 等模型）
- **THEN** 直接展示回答内容
- **AND** 不创建额外的推理 Step
- **AND** 保持向后兼容性

### Requirement: 引用标记可点击链接
系统必须（SHALL）在回答生成过程中将引用标记（如 [1][15]）实时转换为可点击的 Markdown 链接，提供更好的用户交互体验。

#### Scenario: 检测引用标记
- **WHEN** 系统在流式输出中检测到引用标记模式 `[数字]`
- **THEN** 识别引用编号
- **AND** 从 GlobalCitationManager 查找对应的引用信息
- **AND** 准备转换为链接格式

#### Scenario: 转换为 Markdown 链接
- **WHEN** 系统找到引用编号对应的 URL
- **THEN** 将 `[数字]` 转换为 `[数字](URL)` 格式
- **AND** 保持引用编号的可见性
- **AND** 提供直接点击跳转到来源的功能

#### Scenario: 实时转换处理
- **WHEN** 回答内容流式输出时
- **THEN** 系统实时检测和转换引用标记
- **AND** 转换后的内容立即展示给用户
- **AND** 不影响流式输出的实时性

#### Scenario: 处理未找到的引用
- **WHEN** 引用编号在 GlobalCitationManager 中不存在
- **THEN** 保持原始的 `[数字]` 格式
- **AND** 记录警告日志
- **AND** 不中断回答的正常展示

#### Scenario: 处理多个连续引用
- **WHEN** 回答中包含多个连续的引用标记（如 [1][2][3]）
- **THEN** 系统正确识别每个引用编号
- **AND** 分别转换为对应的链接
- **AND** 保持原始的紧凑排列格式

#### Scenario: 引用链接点击体验
- **WHEN** 用户点击引用链接
- **THEN** 在新标签页中打开引用来源
- **AND** 用户可以快速查看来源内容
- **AND** 不需要滚动到页面底部查看引用列表

