## MODIFIED Requirements

### Requirement: 引用编号分配
系统必须（SHALL）根据对话模式采用不同的引用编号策略：Chat 模式使用独立编号（每次从1开始），Agent 模式使用全局连续编号。

#### Scenario: Chat 模式引用编号（保持现有行为）
- **WHEN** 系统处于 Chat 模式并执行搜索
- **THEN** 搜索结果从编号 1 开始分配
- **AND** 每次搜索使用独立的编号序列
- **AND** 行为与现有实现完全一致
- **AND** 不受 Agent 模式引用管理影响

#### Scenario: Agent 模式引用编号（新行为）
- **WHEN** 系统处于 Agent 模式并执行搜索
- **THEN** 搜索结果使用全局引用管理器分配编号
- **AND** 编号连续递增，跨多次搜索保持唯一性
- **AND** 第一次搜索: [1-N], 第二次搜索: [N+1-M]

#### Scenario: CitationProcessor 支持偏移量
- **WHEN** 创建 CitationProcessor 实例
- **THEN** 可以指定 offset 参数（默认为 0）
- **AND** offset = 0 表示从编号 1 开始（Chat 模式）
- **AND** offset > 0 表示从编号 offset+1 开始（Agent 模式）
- **AND** 保持向后兼容，现有调用不需修改

#### Scenario: 编号偏移量计算
- **WHEN** Agent 第二次搜索返回结果
- **THEN** offset = 第一次搜索的结果数量（如 5）
- **AND** 第二次搜索的编号从 6 开始
- **AND** 自动计算和传递偏移量

#### Scenario: 引用映射构建包含偏移
- **WHEN** CitationProcessor 构建引用映射
- **THEN** 映射键 = 原始索引 + offset + 1
- **AND** 例: offset=5, 结果索引 0 → 映射键 6
- **AND** 引用转换使用偏移后的编号

## MODIFIED Requirements

### Requirement: 搜索结果引用
系统必须（SHALL）在 Agent 模式下支持全局连续的搜索结果引用编号，并在最终回答后展示统一的引用列表。

#### Scenario: Agent 模式结果编号分配（修改）
- **WHEN** SearchTool 在 Agent 模式下返回结果
- **THEN** 使用全局引用管理器分配编号
- **AND** 编号连续递增，不从 1 重新开始
- **AND** 工具输出中明确标注全局编号

#### Scenario: Agent 模式引用结果（修改）
- **WHEN** Agent 在回答中引用搜索结果
- **THEN** Agent 使用全局编号 [数字] 格式引用
- **AND** 系统识别并处理全局编号的引用
- **AND** 将引用转换为可点击链接

#### Scenario: Agent 模式引用列表生成（新增）
- **WHEN** Agent 回答完成
- **THEN** 系统生成统一的引用文章列表
- **AND** 列表包含所有搜索的来源信息
- **AND** 按搜索轮次分组展示
- **AND** 添加在回答末尾

#### Scenario: Chat 模式引用列表生成（保持不变）
- **WHEN** Chat 模式回答包含引用
- **THEN** 使用现有的 "参考文献" 格式
- **AND** 行为与之前完全一致
- **AND** 不使用全局引用管理器

