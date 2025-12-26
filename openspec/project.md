# 项目上下文

## 目的

这是一个功能完善的对话式 AI 智能体项目，支持多模型提供商和联网搜索能力。

**目标：**
- ✅ 构建一个功能完善的对话式 AI 智能体
- ✅ 支持多个 LLM 提供商（OpenAI, Anthropic, DeepSeek）
- ✅ 集成联网搜索能力（SearXNG）
- ✅ 流式响应和实时交互
- 🔄 为未来能力扩展奠定基础（RAG、长期记忆等）
- ✅ 创建一个支持增长的模块化架构

## 技术栈

### 核心技术
- **编程语言：** Python 3.11+
- **LLM 框架：** LangChain - 用于模型集成和编排
- **UI 框架：** Chainlit - 用于对话界面和流式响应
- **搜索引擎：** SearXNG - 用于联网搜索能力
- **未来 Web 服务：** FastAPI - 当需要 Web API 端点时使用

### 开发工具
- **依赖管理：** pip + requirements.txt（或稍后使用 Poetry）
- **代码格式化：** black, isort
- **代码检查：** pylint 或 ruff
- **类型检查：** mypy（推荐用于类型提示）

### 关键库
- **LangChain** (v0.1.0) - 核心框架
- **OpenAI SDK** (v1.6.1) - OpenAI API 集成
- **Anthropic SDK** (v0.8.1) - Claude API 集成
- **Chainlit** (v1.0.0) - 对话界面和流式响应
- **Tiktoken** (v0.5.2) - Token 计数
- **HTTPX** - HTTP 客户端用于搜索服务
- **Pydantic** (v2.5.3) - 配置验证和类型安全
- **Tenacity** (v8.2.3) - 重试逻辑和错误处理
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

系统遵循 5 层架构：

```
┌─────────────────────────────────┐
│  应用层 (UI/API)                │  Chainlit/Streamlit/FastAPI
├─────────────────────────────────┤
│  业务层 (Agent/Chains)          │  LangChain agents & chains
├─────────────────────────────────┤
│  搜索/回忆层                     │  RAG, memory, retrieval
├─────────────────────────────────┤
│  模型层                          │  LLMs + Embeddings
├─────────────────────────────────┤
│  数据层                          │  Vector stores, persistence
└─────────────────────────────────┘
```

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
│   │   └── search_config.py   # 搜索配置
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
│   │   └── formatter.py       # 结果格式化
│   ├── agents/          # 🔄 Agent 实现（待开发）
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
- **提示工程：** 基于模板的提示系统，支持变量替换和搜索结果注入
- **流式响应：** 实时生成和显示 AI 响应
- **联网搜索：** 基于 SearXNG 的实时信息检索
- **令牌管理：** 使用 tiktoken 进行精确的 token 计数和验证
- **错误处理：** 自动重试、指数退避、超时控制

**计划中 🔄：**
- **RAG（检索增强生成）：** 将检索与生成相结合
- **ReAct 模式：** 推理 + 行动模式用于智能体行为
- **技能/工具：** 智能体的可扩展能力（函数调用）

### 关键概念

**已实现 ✅：**
- **对话上下文：** 维护对话历史和上下文
- **令牌管理：** 管理上下文窗口限制
- **配置验证：** 基于 Pydantic 的类型安全配置
- **多提供商支持：** 统一接口支持多个 LLM 提供商

**待实现 🔄：**
- **向量嵌入：** 语义搜索和相似度匹配
- **思维链：** 提示中的逐步推理
- **少样本学习：** 在提示中提供示例

### 未来能力（计划中）
- [ ] RAG（检索增强生成）支持
- [ ] 多智能体协作
- [ ] 自定义工具/技能集成
- [ ] 长期记忆系统
- [ ] 多模态交互（图像、音频）
- [ ] 智能搜索触发（自动检测何时需要搜索）
- [ ] 对话导出/导入功能

## 重要约束

**技术约束 ✅：**
- **Token 限制：**
  - OpenAI GPT-4: 最大 8,192 tokens (输入 + 输出)
  - Anthropic Claude: 最大 200,000 tokens (Claude 3)
  - DeepSeek: 最大 4,096 tokens (默认模型)
  - 系统自动验证和计数 token 使用
- **搜索限制：**
  - 默认最多返回 5 条搜索结果
  - 每条结果内容限制 200 字符
  - 搜索超时：5 秒
- **流式响应：**
  - 使用 async/await 模式
  - 实时更新 UI

**运营考虑 ⚠️：**
- **API 速率限制：** 各提供商有不同的速率限制
- **成本管理：** 
  - GPT-4 调用成本较高
  - DeepSeek 提供更经济的选择
  - 搜索使用公共 SearXNG 实例（免费）
- **响应延迟：**
  - 搜索增加 1-3 秒延迟
  - 流式响应改善用户体验
  - 支持重试和超时控制
- **依赖可用性：**
  - 需要稳定的互联网连接
  - SearXNG 公共实例可能不稳定（建议自建）
  - API key 需要有效且有足够额度

## 外部依赖

**当前依赖 ✅：**
- **LLM 提供商 API：**
  - OpenAI API (api.openai.com)
  - Anthropic API (api.anthropic.com)
  - DeepSeek API (api.deepseek.com)
- **搜索服务：**
  - SearXNG 公共实例或私有部署
  - 默认使用 https://searx.be（可配置）
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

**版本：** v1.0 (功能完善的 MVP)  
**最后更新：** 2025-12-26

### 已实现功能 ✅

#### 核心对话能力
- ✅ 基于 Chainlit 的交互式聊天界面
- ✅ 流式响应生成和实时显示
- ✅ 对话历史维护和上下文管理
- ✅ Token 使用跟踪和显示

#### 多模型支持
- ✅ OpenAI GPT-4 集成
- ✅ Anthropic Claude 集成
- ✅ DeepSeek 集成
- ✅ 运行时模型切换 (`/switch` 命令)
- ✅ 统一的模型包装器接口
- ✅ 提供商特定的错误处理

#### 联网搜索
- ✅ SearXNG 集成
- ✅ 实时信息检索
- ✅ 搜索结果格式化和来源引用
- ✅ 可配置的搜索参数
- ✅ 搜索开关控制 (`/search` 命令)

#### 配置管理
- ✅ 基于环境变量的配置
- ✅ Pydantic 配置验证
- ✅ 多提供商配置支持
- ✅ 灵活的参数调整（temperature, max_tokens 等）

#### 错误处理
- ✅ 自动重试机制（指数退避）
- ✅ API 错误处理
- ✅ 超时控制
- ✅ 友好的错误消息

#### 命令系统
- ✅ `/help` - 显示帮助信息
- ✅ `/config` - 查看当前配置
- ✅ `/switch <provider>` - 切换模型提供商
- ✅ `/search <on|off>` - 控制搜索功能
- ✅ `/reset` - 清除对话历史

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

#### 中优先级
- [ ] 智能搜索触发（自动检测何时需要搜索）
- [ ] 对话导出/导入功能
- [ ] 长期对话记忆
- [ ] 用户偏好设置持久化

#### 低优先级
- [ ] 多智能体协作
- [ ] 自定义工具/技能集成
- [ ] 多模态交互（图像、音频）
- [ ] FastAPI REST API 端点

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
- SearXNG 公共实例可能不稳定
- 长对话可能超出 token 限制（需要实现上下文窗口管理）

### 部署状态

- **开发环境：** ✅ 完全支持
- **生产环境：** 🔄 未部署（待配置生产级服务）
- **CI/CD：** ❌ 未配置
