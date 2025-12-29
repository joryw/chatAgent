# AI Agent with Model Invocation

A conversational AI agent with support for multiple LLM providers (OpenAI, Anthropic, DeepSeek) built with LangChain and Chainlit.

## Features

- 🤖 **Multi-Provider Support**: Seamlessly switch between OpenAI, Anthropic, and DeepSeek models
- 🔀 **Dual Conversation Modes**: 
  - **Chat Mode** (💬): Traditional conversation with manual search control
  - **Agent Mode** (🤖): Autonomous AI with ReAct loop for intelligent tool usage
- 💭 **DeepSeek Reasoner**: Advanced reasoning model with transparent thinking process display
- 💬 **Interactive Chat Interface**: Beautiful Chainlit UI for testing and conversation
- 🔍 **Web Search Integration**: Optional SearXNG-powered web search for real-time information
- 🧠 **ReAct Pattern**: Reasoning + Acting loop for complex problem solving
- 🛠️ **Tool Integration**: LangChain-based tool system (search, and extensible for more)
- 🔧 **Configurable Parameters**: Adjust temperature, max_tokens, and other model parameters
- 📝 **Prompt Management**: Template-based prompt system with variable substitution
- 🔄 **Automatic Retry Logic**: Robust error handling with exponential backoff
- 📊 **Token Counting**: Real-time token usage tracking and context validation
- 🎯 **Type-Safe Configuration**: Pydantic-based configuration with validation
- 👁️ **Process Visualization**: Real-time display of agent thinking, tool calls, and results
- 📈 **LangSmith Monitoring**: Optional integration with LangSmith for call tracing, debugging, and performance analysis

## Quick Start

### Prerequisites

- Python 3.11 or higher
- API keys for at least one LLM provider (OpenAI, Anthropic, or DeepSeek)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd chatAgent
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# DeepSeek Configuration (optional)
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=2000

# DeepSeek Model Variant (deepseek-chat or deepseek-reasoner)
# - deepseek-chat: Standard conversational model
# - deepseek-reasoner: Reasoning model with thinking process display
# Note: Can be switched via UI settings panel (recommended)
DEEPSEEK_MODEL_VARIANT=deepseek-chat

# Anthropic Configuration (optional)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_MAX_TOKENS=2000

# Default Provider
DEFAULT_PROVIDER=openai

# Default Conversation Mode (chat or agent)
# - chat: Regular conversation with manual search control
# - agent: Autonomous decision-making with ReAct loop
DEFAULT_MODE=chat

# Logging
LOG_LEVEL=INFO

# Web Search Configuration (optional, requires local SearXNG deployment)
SEARCH_ENABLED=false
SEARXNG_URL=http://localhost:8080  # Local SearXNG instance (recommended)
SEARCH_TIMEOUT=5.0
SEARCH_MAX_RESULTS=5
SEARCH_MAX_CONTENT_LENGTH=200
SEARCH_LANGUAGE=auto
SEARCH_SAFESEARCH=1

# LangSmith Monitoring (optional)
# LangSmith is a monitoring and debugging platform for LangChain applications
# Get your API key from: https://smith.langchain.com/
# If not configured, monitoring is disabled and the application works normally
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=chatagent-dev
# Optional: Custom LangSmith API endpoint (for self-hosted instances)
# LANGSMITH_API_URL=https://api.smith.langchain.com
```

**Note about Web Search:**
- Web search is optional and disabled by default
- **🔥 New: Local SearXNG deployment** - For stable and reliable search functionality
- **🚀 一键部署脚本**: `./deploy-searxng.sh` - 自动完成所有配置！
- **🎯 一键启动**: `./start-all.sh` - 同时启动 SearXNG 和 AI Agent
- **Deployment Guide:** See `docs/guides/deployment/docker.md` for all deployment options
- Enable search in chat using the "🔍 联网搜索" toggle or `/search on` command
- Search results are automatically injected into the model's context with source citations

### Running the Application

Start the Chainlit interface:

```bash
chainlit run app.py -w
```

The `-w` flag enables watch mode for automatic reloading during development.

Open your browser to `http://localhost:8000` to start chatting!

## Usage

### Basic Chat

Simply type your message in the chat interface and press Enter. The agent will respond using the configured model.

### DeepSeek Reasoner Model

DeepSeek offers two model variants:

1. **deepseek-chat** (💬 对话模型): Standard conversational model for general chat
2. **deepseek-reasoner** (💭 推理模型): Advanced reasoning model that shows its thinking process

#### Using DeepSeek Reasoner

**Via UI Settings Panel (Recommended):**
1. Click the ⚙️ icon in the top-right corner
2. Select "🤖 DeepSeek 模型" dropdown
3. Choose "deepseek-reasoner"
4. The model will now display its thinking process before answering

**Via Environment Variable:**
```bash
# In .env file
DEEPSEEK_MODEL_VARIANT=deepseek-reasoner
```

**Features:**
- 💭 **Transparent Thinking**: See the model's reasoning steps in real-time
- 🔄 **Streaming Display**: Thinking content streams as it's generated
- 📦 **Auto-Collapse**: Thinking content automatically collapses when the answer begins
- 🔍 **Expandable**: Click "💡 思考过程" to view the full reasoning process

**Technical Specifications:**

| Specification | deepseek-chat | deepseek-reasoner |
|--------------|---------------|-------------------|
| **Context Length** (Input) | 128K | 128K |
| **Output Length** (max_tokens) | Default 4K, Max **8K** | Default 32K, Max **64K** |
| **Reasoning Display** | ❌ | ✅ |

> **Note**: Context length (128K) refers to how much text the model can **read and understand** (your questions, chat history, etc.), while output length refers to how much text the model can **generate** in response.

**Example Use Cases:**
- Complex problem-solving requiring step-by-step reasoning
- Mathematical calculations with detailed explanations
- Logical deduction and analysis
- Multi-step planning and decision-making

### Conversation Modes

The system supports two distinct conversation modes:

#### 1. Chat Mode (💬) - Default

Traditional conversational AI with manual search control.

**Features:**
- Manual control over web search (via UI toggle or `/search` command)
- Faster responses
- Lower token consumption
- Best for simple conversations and known topics

**Usage:**
- Enable/disable search via UI settings panel (⚙️)
- Or use command: `/search on` or `/search off`

#### 2. Agent Mode (🤖) - Advanced

Autonomous AI that makes intelligent decisions about tool usage.

**Features:**
- 🧠 **Autonomous Decision-Making**: Model decides when to search
- 🔄 **ReAct Loop**: Reasoning → Acting → Observing → Repeat
- 🛠️ **Tool Integration**: Automatic use of search and other tools
- 👁️ **Process Visualization**: See the agent's思考、行动 and 观察过程
- 🎯 **Multi-Step Reasoning**: Supports iterative searches and refinement

**Switching to Agent Mode:**

*Via UI Settings Panel (Recommended):*
1. Click the ⚙️ icon
2. Select **agent** in "🔀 对话模式"
3. Start asking questions

*Via Command:*
```bash
/mode agent
```

**Agent Configuration:**
```bash
# In .env file
DEFAULT_MODE=agent
AGENT_MAX_ITERATIONS=5
AGENT_MAX_EXECUTION_TIME=60
AGENT_VERBOSE=true
```

**How It Works:**

When you ask a question in Agent mode:
1. **💭 思考**: Agent analyzes the question and plans its approach
2. **🛠️ 行动**: If needed, calls search tool to gather information
3. **💡 观察**: Processes the search results
4. **🔁 迭代**: Repeats if more information is needed
5. **✅ 回答**: Provides final answer with citations

**Best Use Cases:**
- Questions requiring real-time information
- Complex queries needing multiple sources
- When unsure if search is needed (let Agent decide)
- Research and fact-checking tasks

**Example:**
```
User: "Compare the latest AI models from OpenAI, Anthropic, and DeepSeek"

Agent Process:
├─ 💭 Thinking: Need current information about latest models
├─ 🛠️ Search: "latest AI models 2024 OpenAI Anthropic DeepSeek"
├─ 💡 Observation: Found 5 results with model comparisons
├─ 💭 Thinking: Information sufficient, can now answer
└─ ✅ Answer: Detailed comparison with citations [1][2][3]
```

For more details, see the [Agent Mode Guide](docs/guides/agent-mode.md).

### Web Search (SearXNG Integration)

**🚀 Prerequisites:** Deploy SearXNG locally for stable search functionality.

See **[SearXNG Deployment Guide](docs/guides/searxng-deployment.md)** for detailed instructions.

#### Quick Deployment (3种方式任选)

**🔥 方式1: 一键脚本 (最简单，推荐)**
```bash
# 一条命令完成所有配置!
./deploy-searxng.sh

# 启动全部服务
./start-all.sh
```

**方式2: 手动 Docker Compose**
```bash
# 1. Deploy SearXNG using Docker
mkdir -p ~/searxng-local
cd ~/searxng-local
curl -O https://raw.githubusercontent.com/searxng/searxng/master/utils/docker-compose.yaml
docker compose up -d

# 2. Configure settings.yml (ensure JSON API is enabled)
# See docs/guides/searxng-deployment.md for details

# 3. Verify deployment
bash openspec/changes/update-searxng-local-deployment/verify-searxng.sh

# 4. Update .env in chatAgent
echo "SEARXNG_URL=http://localhost:8080" >> .env
echo "SEARCH_ENABLED=true" >> .env
```

**方式3: 完整容器化**
```bash
# 使用 docker-compose 同时部署 SearXNG 和 AI Agent
docker-compose -f docker-compose.full.yml up -d
```

📖 **详细部署指南**: [docs/guides/deployment/docker.md](docs/guides/deployment/docker.md)

#### Using Web Search

Once SearXNG is deployed and configured:

1. Type `/search on` in the chat to enable search
2. Type `/search off` to disable search
3. Ask questions that require current information

When search is enabled:
- The system automatically searches for relevant information using your local SearXNG
- Search results are displayed with sources
- The model uses search results to provide up-to-date answers
- Sources are cited with [number] references

**Commands:**
- `/search on` - Enable web search
- `/search off` - Disable web search
- `/search` - Check current search status

**Troubleshooting:**
- If search isn't working, check `docs/guides/troubleshooting/searxng.md`
- Verify SearXNG is running: `docker ps -f name=searxng`
- Check JSON API: `curl "http://localhost:8080/search?q=test&format=json"`

### Slash Commands

The application supports several commands:

- `/help` - Show available commands and usage guide
- `/config` - View current model and mode configuration
- `/mode <chat|agent>` - Switch conversation mode
  - Example: `/mode agent` - Switch to Agent mode
  - Example: `/mode chat` - Switch to Chat mode
- `/switch <provider>` - Switch to a different model provider
  - Example: `/switch deepseek`
- `/search <on|off>` - Enable/disable web search (Chat mode only)
- `/reset` - Clear conversation history

### Switching Providers

To switch between different LLM providers during a conversation:

```
/switch openai      # Switch to OpenAI GPT-4
/switch deepseek    # Switch to DeepSeek
/switch anthropic   # Switch to Anthropic Claude
```

## Project Structure

```
chatAgent/
├── src/
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   ├── model_config.py  # Model settings and validation
│   │   ├── search_config.py # Search settings
│   │   └── agent_config.py  # Agent mode settings
│   ├── models/              # Model wrappers
│   │   ├── __init__.py
│   │   ├── base.py          # Base wrapper interface
│   │   ├── openai_wrapper.py
│   │   ├── deepseek_wrapper.py
│   │   ├── anthropic_wrapper.py
│   │   └── factory.py       # Model wrapper factory
│   ├── agents/              # Agent mode implementation (NEW)
│   │   ├── __init__.py
│   │   ├── base.py          # Base agent interface
│   │   ├── react_agent.py   # ReAct agent with LangChain
│   │   └── tools/           # Agent tools
│   │       ├── __init__.py
│   │       └── search_tool.py # Search tool wrapper
│   ├── prompts/             # Prompt management
│   │   ├── __init__.py
│   │   ├── templates.py     # Prompt templates and utilities
│   │   └── agent_prompts.py # Agent-specific prompts (NEW)
│   └── search/              # Web search module
│       ├── __init__.py
│       ├── models.py         # Search data models
│       ├── searxng_client.py # SearXNG API client
│       ├── search_service.py # Search service
│       ├── formatter.py      # Result formatting
│       └── citation_processor.py # Citation processing (NEW)
├── app.py                   # Main Chainlit application
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create from .env.example)
├── .gitignore
└── README.md
```

## Architecture

The system follows a 5-layer architecture with dual conversation modes:

```
┌─────────────────────────────────────────────────────┐
│  Application Layer (UI/API)     │  Chainlit UI      │
│  - Mode Selection                                   │
│  - Settings Management                              │
│  - Conversation Routing                             │
├─────────────────────────────────────────────────────┤
│  Business Layer (Agents)        │  🤖 Agent Mode    │
│  - ReAct Agent (LangChain)      │  💬 Chat Mode     │
│  - Tool Management              │  Manual control   │
│  - Autonomous Decision-Making   │  Direct LLM call  │
├─────────────────────────────────────────────────────┤
│  Search/Memory Layer            │  SearXNG search   │
│  - SearchService                │  (as tool or      │
│  - Citation Processing          │   manual toggle)  │
│  - Result Formatting            │  RAG (future)     │
├─────────────────────────────────────────────────────┤
│  Model Layer                    │  Multi-Provider   │
│  - LLM wrappers                 │  OpenAI           │
│  - Error handling               │  DeepSeek         │
│  - LangChain integration        │  Anthropic        │
├─────────────────────────────────────────────────────┤
│  Data Layer                     │  Vector stores    │
│  - Configuration                │  (future)         │
│  - Prompts                      │                   │
└─────────────────────────────────────────────────────┘
```

**Conversation Flow:**

```
User Input
    │
    ├── Mode: Chat ──→ handle_chat_mode()
    │                     │
    │                     ├── Manual Search?
    │                     │   ├── Yes → SearchService → Results + LLM
    │                     │   └── No → Direct LLM Call
    │                     └── Stream Response → UI
    │
    └── Mode: Agent ─→ handle_agent_mode()
                          │
                          └── ReActAgent.stream()
                              │
                              ├── 💭 Reasoning (LLM)
                              ├── 🛠️ Action Decision
                              │   └── search_tool?
                              │       ├── Yes → SearchService
                              │       └── No → Skip
                              ├── 💡 Observation
                              ├── 🔁 Repeat if needed
                              └── ✅ Final Answer → UI
```

## Configuration

### Model Parameters

All model parameters can be configured via environment variables:

- **temperature** (0.0-2.0): Controls randomness. Higher = more creative, lower = more deterministic.
- **max_tokens** (positive integer): Maximum tokens to generate in response.
- **top_p** (0.0-1.0): Nucleus sampling parameter.
- **timeout** (seconds): API request timeout.

### Provider-Specific Settings

#### OpenAI
- Uses tiktoken for accurate token counting
- Supports all GPT-4 and GPT-3.5 models
- Integrated with LangChain for advanced features

#### DeepSeek
- OpenAI-compatible API
- Custom base URL support
- Cost-effective alternative to OpenAI

#### Anthropic
- Claude models (Sonnet, Opus, etc.)
- Direct Anthropic SDK integration
- Character-based token estimation

### LangSmith Monitoring (Optional)

LangSmith provides comprehensive monitoring and debugging capabilities for LangChain applications.

**Features:**
- 📊 **Call Tracing**: Automatic tracking of all model calls, Agent executions, and tool invocations
- 🔍 **Debugging**: Detailed view of execution chains and intermediate states
- 📈 **Performance Metrics**: Latency, token usage, and cost tracking
- 🎯 **Project Organization**: Organize traces by project/environment

**Setup:**

1. **Sign up for LangSmith** (free tier available):
   - Visit https://smith.langchain.com/
   - Create an account and get your API key

2. **Configure in `.env`**:
   ```bash
   LANGSMITH_API_KEY=your-api-key-here
   LANGSMITH_PROJECT=chatagent-dev  # Optional: project name
   ```

3. **Restart the application** - LangSmith monitoring will be automatically enabled

**What Gets Tracked:**
- ✅ All model invocations (OpenAI, Anthropic, DeepSeek)
- ✅ Agent execution steps (thinking, tool calls, observations)
- ✅ Tool invocations (web search, etc.)
- ✅ Performance metrics (latency, token usage)
- ✅ Error traces and debugging information

**Project Organization:**
Use different project names for different environments:
```bash
# Development
LANGSMITH_PROJECT=chatagent-dev

# Production
LANGSMITH_PROJECT=chatagent-prod

# Testing
LANGSMITH_PROJECT=chatagent-test
```

**Note:** If `LANGSMITH_API_KEY` is not configured, monitoring is automatically disabled and the application works normally. This ensures backward compatibility.

## Error Handling

The system implements robust error handling:

1. **Rate Limiting**: Automatic retry with exponential backoff (HTTP 429)
2. **Authentication Errors**: Immediate failure with clear error message
3. **Network Timeouts**: Configurable timeout with retry logic
4. **Validation Errors**: Configuration validation at startup

## Token Management

- Real-time token counting using tiktoken (for OpenAI/DeepSeek)
- Context window validation before API calls
- Token usage tracking in response metadata
- Warnings when approaching context limits

## Development

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Maximum line length: 88 characters (black default)
- Use docstrings (Google or NumPy format)

### Adding a New Provider

1. Create a new wrapper in `src/models/<provider>_wrapper.py`
2. Inherit from `BaseModelWrapper`
3. Implement required methods: `generate()` and `count_tokens()`
4. Add provider to `ModelProvider` enum in `model_config.py`
5. Update factory in `factory.py`

Example:

```python
from .base import BaseModelWrapper, ModelResponse

class NewProviderWrapper(BaseModelWrapper):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        # Initialize provider client
    
    async def generate(self, prompt: str, system_message: Optional[str] = None, **kwargs) -> ModelResponse:
        # Implement generation logic
        pass
    
    def count_tokens(self, text: str) -> int:
        # Implement token counting
        pass
```

## Troubleshooting

### Common Issues

1. **"Invalid API key" error**
   - Check that your `.env` file exists and contains valid API keys
   - Ensure keys don't start with placeholder text like "sk-your-"

2. **"No model providers configured"**
   - At least one provider must have a valid API key configured
   - Check `DEFAULT_PROVIDER` setting matches an available provider

3. **Import errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Activate your virtual environment

4. **Token limit exceeded**
   - Reduce `max_tokens` in configuration
   - Shorten your input prompt
   - Use `/reset` to clear conversation history

## Recent Updates

- 🤖 **Agent Mode** - NEW! Autonomous AI with ReAct pattern
  - LangChain-based agent with intelligent tool usage
  - Real-time visualization of思考、行动 and 观察过程
  - Automatic decision-making for web search
  - Multi-step reasoning and iterative refinement
  - See `docs/guides/agent-mode.md` for full details
- 🔥 **Local SearXNG Deployment** - Stable web search via local Docker deployment
  - Complete deployment guide with docker-compose.yml and settings.yml templates
  - Enhanced health checks and configuration validation
  - Automatic troubleshooting and error diagnostics
  - See `docs/guides/searxng-deployment.md`
- ✅ **Web Search Integration** - SearXNG-powered search with source display (also available as Agent tool)
- ✅ **Streaming Responses** - Real-time response generation
- ✅ **Multi-Provider Support** - OpenAI, Anthropic, DeepSeek

## Future Enhancements

- [ ] RAG (Retrieval Augmented Generation) support
- [ ] Long-term conversation memory
- [ ] Multi-agent collaboration
- [ ] Custom tool/skill integration
- [ ] Conversation export/import
- [ ] Advanced prompt engineering features
- [ ] Smart search triggering (auto-detect when search is needed)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please follow the existing code style and add tests for new features.

## Documentation

📚 **Complete documentation is available in the [docs/](docs/) directory.**

### Quick Links

- 🚀 [Quick Start Guide](docs/guides/quick-start/) - Get started in 5 minutes
- 🐳 [Docker Deployment Guide](docs/guides/deployment/docker.md) - **NEW:** 3种部署方式 (含一键脚本)
- 🔍 [SearXNG Deployment Guide](docs/guides/searxng-deployment.md) - Local search setup
- 🔧 [SearXNG Troubleshooting](docs/guides/troubleshooting/searxng.md) - Fix search issues
- ⚙️ [Configuration Guide](docs/guides/configuration/) - Detailed configuration options
- 🏗️ [Architecture Overview](docs/architecture/overview/) - System design and architecture
- 👨‍💻 [Contributing Guide](docs/development/contributing/) - How to contribute
- 🔧 [Troubleshooting](docs/operations/troubleshooting/) - Common issues and solutions
- 📖 [API Documentation](docs/api/) - API reference (coming soon)

### Documentation Structure

```
docs/
├── architecture/     # System architecture and design decisions
├── development/      # Developer guides and coding standards
├── guides/          # User guides and tutorials
├── api/             # API documentation
├── operations/      # Deployment and troubleshooting
└── templates/       # Document templates
```

### Language Support

- 🇨🇳 中文文档: 查看 [docs/README.md](docs/README.md)
- 🇬🇧 English docs: See [docs/README.md](docs/README.md)

## Support

For issues and questions, please open an issue on the GitHub repository.

