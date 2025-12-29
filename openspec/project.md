# 项目上下文

## 目的

这是一个功能完善的对话式 AI 智能体项目，支持多模型提供商、双对话模式和联网搜索能力。

**目标：**
- ✅ 构建一个功能完善的对话式 AI 智能体
- ✅ 支持多个 LLM 提供商（OpenAI, Anthropic, DeepSeek）
- ✅ 双对话模式：Chat Mode（手动控制）和 Agent Mode（自主决策）
- ✅ ReAct 模式实现：推理 + 行动循环
- ✅ 集成联网搜索能力（SearXNG）
- ✅ 流式响应和实时交互
- ✅ DeepSeek Reasoner 支持（透明思考过程显示）
- ✅ LangSmith 监控集成（可选）
- 🔄 为未来能力扩展奠定基础（RAG、长期记忆等）
- ✅ 创建一个支持增长的模块化架构

## 技术栈

### 核心技术
- **编程语言：** Python 3.11+
- **LLM 框架：** LangChain - 用于模型集成和编排
- **Agent 框架：** LangGraph - 用于 Agent 工作流和状态管理
- **UI 框架：** Chainlit - 用于对话界面和流式响应
- **搜索引擎：** SearXNG - 用于联网搜索能力
- **监控平台：** LangSmith - 用于调用追踪、调试和性能分析（可选）
- **未来 Web 服务：** FastAPI - 当需要 Web API 端点时使用

### 开发工具
- **依赖管理：** pip + requirements.txt（或稍后使用 Poetry）
- **代码格式化：** black, isort
- **代码检查：** pylint 或 ruff
- **类型检查：** mypy（推荐用于类型提示）

### 关键库
- **LangChain** (>=0.1.0) - 核心框架和 Agent 支持
- **LangGraph** (>=1.0.0) - Agent 工作流和状态管理
- **LangSmith** (>=0.1.0) - 监控和调试平台（可选）
- **OpenAI SDK** (>=1.6.1) - OpenAI API 集成
- **Anthropic SDK** (>=0.8.1) - Claude API 集成
- **Chainlit** (>=1.0.0) - 对话界面和流式响应
- **Tiktoken** (>=0.5.2) - Token 计数
- **HTTPX** (>=0.23.0) - HTTP 客户端用于搜索服务
- **Pydantic** (>=2.5.3) - 配置验证和类型安全
- **Tenacity** (>=8.2.3) - 重试逻辑和错误处理
- 向量存储（待实现：ChromaDB、Pinecone 或 Faiss）
- 嵌入模型（待实现：OpenAI、Sentence Transformers 等）

## 项目约定

### 代码风格

**Python 标准：**
- 遵循 PEP 8 风格指南
- 为函数签名使用类型提示
- 最大行长度：88 个字符（black 默认值）
- 使用描述性的变量和函数名称

**命名约定：**
- 函数/方法：`snake_case`（例如，`process_user_query`）
- 类：`PascalCase`（例如，`AgentController`）
- 常量：`UPPER_SNAKE_CASE`（例如，`MAX_TOKENS`）
- 私有方法：使用 `_` 前缀（例如，`_internal_helper`）

**文档：**
- 为所有公共函数和类使用文档字符串
- 遵循 Google 或 NumPy 文档字符串格式
- 除了文档字符串外，还要包含类型提示

**示例：**
```python
def process_message(user_input: str, context: dict) -> str:
    """处理用户消息并生成响应。
    
    Args:
        user_input: 用户的消息文本
        context: 对话上下文字典
        
    Returns:
        生成的响应字符串
    """
    # 实现
    pass
```

### 架构模式

系统遵循 5 层架构，支持双对话模式：

```
┌─────────────────────────────────────────────────────┐
│  应用层 (UI/API)                │  Chainlit UI      │
│  - 模式选择 (Chat/Agent)                            │
│  - 设置管理                                          │
│  - 对话路由                                          │
├─────────────────────────────────────────────────────┤
│  业务层 (Agents)              │  🤖 Agent Mode    │
│  - ReAct Agent (LangChain)    │  💬 Chat Mode     │
│  - 工具管理                    │  手动控制          │
│  - 自主决策                    │  直接 LLM 调用     │
├─────────────────────────────────────────────────────┤
│  搜索/回忆层                   │  SearXNG 搜索     │
│  - SearchService               │  (作为工具或       │
│  - Citation Processing         │   手动开关)       │
│  - Result Formatting           │  RAG (未来)       │
├─────────────────────────────────────────────────────┤
│  模型层                        │  多提供商          │
│  - LLM wrappers                │  OpenAI           │
│  - Error handling              │  DeepSeek         │
│  - LangChain integration       │  Anthropic        │
├─────────────────────────────────────────────────────┤
│  数据层                        │  Vector stores    │
│  - Configuration               │  (未来)           │
│  - Prompts                     │                   │
└─────────────────────────────────────────────────────┘
```

**对话流程：**
- **Chat Mode**: 用户手动控制搜索，直接调用 LLM
- **Agent Mode**: ReAct 循环，Agent 自主决定何时使用工具（搜索）

**设计原则：**
- 每层都有明确的职责
- 依赖向下流动（高层依赖低层）
- 使用依赖注入以提高可测试性
- 将业务逻辑与 UI/API 逻辑分离
- 使用配置文件管理模型参数和 API 密钥

**项目结构：**
```
chatAgent/
├── src/
│   ├── config/          # ✅ 配置管理
│   │   ├── model_config.py    # 模型配置和验证
│   │   ├── search_config.py   # 搜索配置
│   │   ├── agent_config.py    # Agent 模式配置
│   │   └── langsmith_config.py # LangSmith 监控配置
│   ├── models/          # ✅ 模型封装层
│   │   ├── base.py            # 基础模型接口
│   │   ├── openai_wrapper.py  # OpenAI 封装
│   │   ├── anthropic_wrapper.py # Anthropic 封装
│   │   ├── deepseek_wrapper.py  # DeepSeek 封装
│   │   └── factory.py         # 模型工厂
│   ├── prompts/         # ✅ 提示模板管理
│   │   └── templates.py       # 提示模板和工具
│   ├── search/          # ✅ 联网搜索组件
│   │   ├── models.py          # 数据模型
│   │   ├── searxng_client.py  # SearXNG 客户端
│   │   ├── search_service.py  # 搜索服务
│   │   ├── formatter.py       # 结果格式化
│   │   └── citation_processor.py # 引用处理
│   ├── agents/          # ✅ Agent 实现
│   │   ├── base.py            # Agent 基础接口
│   │   ├── react_agent.py     # ReAct Agent 实现
│   │   └── tools/             # Agent 工具
│   │       └── search_tool.py # 搜索工具包装
│   ├── chains/          # 🔄 LangChain 链（待开发）
│   ├── retrieval/       # 🔄 RAG 组件（待开发）
│   └── data/            # 🔄 数据访问层（待开发）
├── docs/                # ✅ 完整文档体系
│   ├── architecture/    # 架构设计文档
│   ├── guides/          # 用户指南
│   ├── development/     # 开发者指南
│   ├── operations/      # 运维文档
│   └── api/             # API 文档（待开发）
├── openspec/            # ✅ OpenSpec 规范管理
│   ├── project.md       # 项目上下文
│   ├── specs/           # 功能规范
│   │   ├── agent-mode/        # Agent 模式规范
│   │   ├── model-invocation/  # 模型调用规范
│   │   ├── web-search/         # 搜索功能规范
│   │   └── dev-doc-management/ # 文档管理规范
│   └── changes/         # 变更提案
├── tests/               # 🔄 测试文件（待开发）
├── app.py               # ✅ Chainlit 主应用
├── requirements.txt     # ✅ Python 依赖
└── README.md            # ✅ 项目说明
```

### 测试策略

**阶段 1 - 手动测试（当前）：**
- 通过 UI 交互验证对话能力
- 手动测试不同的用户查询和场景
- 记录边界情况和失败模式

**阶段 2 - 自动化测试（未来）：**
- 为单个组件编写单元测试（agents、chains、utilities）
- 为端到端流程编写集成测试
- 测试覆盖率目标：关键路径 >70%

**测试工具（需要时）：**
- pytest 作为测试框架
- pytest-asyncio 用于异步测试
- unittest.mock 用于模拟 LLM 调用

### Git 工作流

**分支策略：**
- `master` - 稳定的、可用于生产的代码
- `dev` - 开发分支（当项目扩展时引入）
- 功能分支 - 用于特定功能（需要时从 `dev` 创建）

**当前实践（MVP 阶段）：**
- 直接在 `master` 上开发以快速迭代
- 随着项目成熟过渡到 `dev` 分支工作流

**提交消息格式：**
```
<type>: <subject>

[optional body]
```

**提交类型：**
- `feat` - 新功能
- `fix` - Bug 修复
- `refactor` - 代码重构（无行为变化）
- `docs` - 文档更改
- `test` - 添加或修改测试
- `chore` - 构建脚本、依赖、工具

**示例：**
```
feat: add conversation memory to agent
fix: resolve token limit exceeded error
refactor: extract prompt templates to separate module
docs: update README with setup instructions
```

## 领域上下文

### 核心技术

**已实现 ✅：**
- **大型语言模型（LLMs）：** 支持 GPT-4、Claude、DeepSeek 等多个模型
- **DeepSeek Reasoner：** 支持推理模型，透明显示思考过程
- **提示工程：** 基于模板的提示系统，支持变量替换和搜索结果注入
- **流式响应：** 实时生成和显示 AI 响应
- **联网搜索：** 基于 SearXNG 的实时信息检索
- **ReAct 模式：** 推理 + 行动循环，用于 Agent 自主决策
- **双对话模式：** Chat Mode（手动控制）和 Agent Mode（自主决策）
- **令牌管理：** 使用 tiktoken 进行精确的 token 计数和验证
- **错误处理：** 自动重试、指数退避、超时控制
- **LangSmith 监控：** 可选的调用追踪、调试和性能分析

**计划中 🔄：**
- **RAG（检索增强生成）：** 将检索与生成相结合
- **技能/工具扩展：** 更多智能体工具（函数调用）
- **向量数据库集成：** 用于 RAG 和长期记忆

### 关键概念

**已实现 ✅：**
- **对话上下文：** 维护对话历史和上下文
- **令牌管理：** 管理上下文窗口限制
- **配置验证：** 基于 Pydantic 的类型安全配置
- **多提供商支持：** 统一接口支持多个 LLM 提供商
- **ReAct 循环：** 思考 → 行动 → 观察 → 迭代
- **工具调用：** Agent 自主决定何时使用搜索工具
- **过程可视化：** 实时显示 Agent 的思考、行动和观察过程
- **引用处理：** 搜索结果自动添加来源引用

**待实现 🔄：**
- **向量嵌入：** 语义搜索和相似度匹配
- **思维链：** 提示中的逐步推理（部分通过 DeepSeek Reasoner 实现）
- **少样本学习：** 在提示中提供示例

### 未来能力（计划中）
- [ ] RAG（检索增强生成）支持
- [ ] 向量数据库集成（ChromaDB、Pinecone 或 Faiss）
- [ ] 文档上传和知识库管理
- [ ] 多智能体协作
- [ ] 更多自定义工具/技能集成
- [ ] 长期记忆系统
- [ ] 多模态交互（图像、音频）
- [ ] 对话导出/导入功能
- [ ] FastAPI REST API 端点

## 重要约束

**技术约束 ✅：**
- **Token 限制：**
  - OpenAI GPT-4: 最大 8,192 tokens (输入 + 输出)
  - Anthropic Claude: 最大 200,000 tokens (Claude 3)
  - DeepSeek Chat: 最大 4,096 tokens (默认模型)
  - DeepSeek Reasoner: 输入 128K tokens，输出最大 64K tokens
  - 系统自动验证和计数 token 使用
- **Agent 模式限制：**
  - 最大迭代次数：5 次（可配置，范围 1-10）
  - 最大执行时间：60 秒（可配置，范围 10-300 秒）
- **搜索限制：**
  - 默认最多返回 5 条搜索结果
  - 每条结果内容限制 200 字符
  - 搜索超时：5 秒
- **流式响应：**
  - 使用 async/await 模式
  - 实时更新 UI
  - 支持思考过程和最终答案的分离显示

**运营考虑 ⚠️：**
- **API 速率限制：** 各提供商有不同的速率限制
- **成本管理：** 
  - GPT-4 调用成本较高
  - DeepSeek 提供更经济的选择
  - Agent Mode 可能产生多次 LLM 调用（每次迭代）
  - 搜索使用本地 SearXNG 部署（推荐）或公共实例（免费但不稳定）
- **响应延迟：**
  - 搜索增加 1-3 秒延迟
  - Agent Mode 可能增加延迟（多步迭代）
  - 流式响应改善用户体验
  - 支持重试和超时控制
- **依赖可用性：**
  - 需要稳定的互联网连接
  - SearXNG 建议本地部署（Docker）以获得稳定搜索
  - API key 需要有效且有足够额度
  - LangSmith 监控为可选功能，不影响核心功能

## 外部依赖

**当前依赖 ✅：**
- **LLM 提供商 API：**
  - OpenAI API (api.openai.com)
  - Anthropic API (api.anthropic.com)
  - DeepSeek API (api.deepseek.com)
- **搜索服务：**
  - SearXNG 本地部署（推荐，Docker）或公共实例
  - 默认使用本地 http://localhost:8080（可配置）
- **监控服务（可选）：**
  - LangSmith API (api.smith.langchain.com)
  - 用于调用追踪、调试和性能分析
- **Python 包管理：**
  - PyPI 用于依赖安装

**计划依赖 🔄：**
- 向量数据库（如果使用云服务）
  - ChromaDB
  - Pinecone
  - 或 Faiss（本地）
- 智能体技能的潜在第三方工具/API

**配置管理：**
- ✅ 在环境变量中存储 API 密钥和机密
- ✅ 使用 `.env` 文件进行本地开发（已加入 .gitignore）
- ✅ 在 README 中记录所有必需的环境变量
- ✅ 使用 Pydantic 进行配置验证
- ✅ 支持环境变量覆盖默认配置

## 项目当前状态

**版本：** v2.0 (支持 Agent Mode 和 ReAct 模式)  
**最后更新：** 2025-01-XX

### 已实现功能 ✅

#### 核心对话能力
- ✅ 基于 Chainlit 的交互式聊天界面
- ✅ 双对话模式：Chat Mode 和 Agent Mode
- ✅ 流式响应生成和实时显示
- ✅ 对话历史维护和上下文管理
- ✅ Token 使用跟踪和显示
- ✅ 模式切换功能（`/mode` 命令）

#### 多模型支持
- ✅ OpenAI GPT-4 集成
- ✅ Anthropic Claude 集成
- ✅ DeepSeek Chat 集成
- ✅ DeepSeek Reasoner 集成（透明思考过程显示）
- ✅ 运行时模型切换 (`/switch` 命令)
- ✅ 统一的模型包装器接口
- ✅ LangChain 集成（支持 Agent 和工具调用）
- ✅ 提供商特定的错误处理

#### 联网搜索
- ✅ SearXNG 集成（支持本地部署和公共实例）
- ✅ 实时信息检索
- ✅ 搜索结果格式化和来源引用
- ✅ 引用自动处理和编号
- ✅ 可配置的搜索参数
- ✅ 搜索开关控制 (`/search` 命令，Chat Mode）
- ✅ Agent Mode 中作为工具自动调用

#### Agent Mode（ReAct 模式）
- ✅ ReAct Agent 实现（基于 LangChain）
- ✅ 自主决策工具使用（搜索）
- ✅ 多步迭代推理和行动循环
- ✅ 实时过程可视化（思考、行动、观察）
- ✅ 可配置的迭代次数和执行时间
- ✅ 支持独立的函数调用模型和答案生成模型

#### 配置管理
- ✅ 基于环境变量的配置
- ✅ Pydantic 配置验证
- ✅ 多提供商配置支持
- ✅ Agent 模式专用配置
- ✅ LangSmith 监控配置（可选）
- ✅ 灵活的参数调整（temperature, max_tokens 等）

#### 错误处理
- ✅ 自动重试机制（指数退避）
- ✅ API 错误处理
- ✅ 超时控制
- ✅ 友好的错误消息

#### 命令系统
- ✅ `/help` - 显示帮助信息
- ✅ `/config` - 查看当前配置
- ✅ `/mode <chat|agent>` - 切换对话模式
- ✅ `/switch <provider>` - 切换模型提供商
- ✅ `/search <on|off>` - 控制搜索功能（Chat Mode）
- ✅ `/reset` - 清除对话历史

#### 监控和调试
- ✅ LangSmith 集成（可选）
- ✅ 调用追踪和链式执行可视化
- ✅ 性能指标收集（延迟、token 使用）
- ✅ 错误追踪和调试信息

#### 文档体系
- ✅ 完整的项目文档（docs/ 目录）
- ✅ 架构设计文档
- ✅ 用户指南和快速开始
- ✅ 开发者贡献指南
- ✅ OpenSpec 规范管理

### 待实现功能 🔄

#### 高优先级
- [ ] RAG（检索增强生成）支持
- [ ] 向量数据库集成（ChromaDB/Pinecone）
- [ ] 文档上传和知识库管理
- [ ] 自动化测试套件
- [ ] 上下文窗口管理（长对话处理）

#### 中优先级
- [ ] 更多 Agent 工具（计算器、代码执行等）
- [ ] 对话导出/导入功能
- [ ] 长期对话记忆
- [ ] 用户偏好设置持久化
- [ ] Agent 工具结果缓存优化

#### 低优先级
- [ ] 多智能体协作
- [ ] 自定义工具/技能集成框架
- [ ] 多模态交互（图像、音频）
- [ ] FastAPI REST API 端点
- [ ] WebSocket 实时通信支持

### 技术债务和改进机会

- [ ] 添加单元测试和集成测试
- [ ] 实现日志轮转和管理
- [ ] 优化搜索结果缓存
- [ ] 添加性能监控和指标
- [ ] 支持更多搜索引擎（Google, Bing 等）
- [ ] 改进 token 计数的准确性（对于非 OpenAI 模型）

### 已知问题

- DeepSeek 的 token 计数基于估算（使用 tiktoken）
- Anthropic 的 token 计数基于字符数估算
- SearXNG 公共实例可能不稳定（建议使用本地部署）
- 长对话可能超出 token 限制（需要实现上下文窗口管理）
- Agent Mode 可能产生较高的 API 调用成本（多次迭代）
- DeepSeek Reasoner 的思考内容不计入最终答案的 token 限制

### 部署状态

- **开发环境：** ✅ 完全支持
- **本地部署：** ✅ 支持 Docker Compose 一键部署（SearXNG + AI Agent）
- **生产环境：** 🔄 未部署（待配置生产级服务）
- **CI/CD：** ❌ 未配置
- **监控：** ✅ LangSmith 集成（可选，开发调试用）

### OpenSpec 规范

项目使用 OpenSpec 进行规范驱动开发：

**当前规范：**
- ✅ `agent-mode` - Agent Mode 和 ReAct 模式规范
- ✅ `model-invocation` - 模型调用规范
- ✅ `web-search` - 联网搜索功能规范
- ✅ `dev-doc-management` - 文档管理规范

**规范位置：** `openspec/specs/`
**变更提案：** `openspec/changes/`
