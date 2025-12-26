# AI Agent with Model Invocation

A conversational AI agent with support for multiple LLM providers (OpenAI, Anthropic, DeepSeek) built with LangChain and Chainlit.

## Features

- 🤖 **Multi-Provider Support**: Seamlessly switch between OpenAI, Anthropic, and DeepSeek models
- 💬 **Interactive Chat Interface**: Beautiful Chainlit UI for testing and conversation
- 🔍 **Web Search Integration**: Optional SearXNG-powered web search for real-time information
- 🔧 **Configurable Parameters**: Adjust temperature, max_tokens, and other model parameters
- 📝 **Prompt Management**: Template-based prompt system with variable substitution
- 🔄 **Automatic Retry Logic**: Robust error handling with exponential backoff
- 📊 **Token Counting**: Real-time token usage tracking and context validation
- 🎯 **Type-Safe Configuration**: Pydantic-based configuration with validation

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

# Anthropic Configuration (optional)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_MAX_TOKENS=2000

# Default Provider
DEFAULT_PROVIDER=openai

# Logging
LOG_LEVEL=INFO

# Web Search Configuration (optional)
SEARCH_ENABLED=false
SEARXNG_URL=https://searx.be
SEARCH_TIMEOUT=5.0
SEARCH_MAX_RESULTS=5
SEARCH_MAX_CONTENT_LENGTH=200
SEARCH_LANGUAGE=auto
SEARCH_SAFESEARCH=1
```

**Note about Web Search:**
- Web search is optional and disabled by default
- You can use public SearXNG instances (like https://searx.be) or deploy your own
- Enable it in the chat interface using the "🔍 联网搜索" toggle
- Search results are automatically injected into the model's context

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

### Web Search

Enable web search to get real-time information from the internet:

1. Type `/search on` in the chat to enable search
2. Type `/search off` to disable search
3. Ask questions that require current information

When search is enabled:
- The system automatically searches for relevant information
- Search results are displayed with sources
- The model uses search results to provide up-to-date answers
- Sources are cited with [number] references

**Commands:**
- `/search on` - Enable web search
- `/search off` - Disable web search
- `/search` - Check current search status

### Slash Commands

The application supports several commands:

- `/help` - Show available commands
- `/config` - View current model configuration
- `/switch <provider>` - Switch to a different model provider
  - Example: `/switch deepseek`
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
│   │   └── search_config.py # Search settings
│   ├── models/              # Model wrappers
│   │   ├── __init__.py
│   │   ├── base.py          # Base wrapper interface
│   │   ├── openai_wrapper.py
│   │   ├── deepseek_wrapper.py
│   │   ├── anthropic_wrapper.py
│   │   └── factory.py       # Model wrapper factory
│   ├── prompts/             # Prompt management
│   │   ├── __init__.py
│   │   └── templates.py     # Prompt templates and utilities
│   └── search/              # Web search module
│       ├── __init__.py
│       ├── models.py         # Search data models
│       ├── searxng_client.py # SearXNG API client
│       ├── search_service.py # Search service
│       └── formatter.py      # Result formatting
├── app.py                   # Main Chainlit application
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create from .env.example)
├── .gitignore
└── README.md
```

## Architecture

The system follows a 5-layer architecture:

```
┌─────────────────────────────────┐
│  Application Layer (UI/API)     │  Chainlit interface
├─────────────────────────────────┤
│  Business Layer (Agent/Chains)  │  LangChain agents (future)
├─────────────────────────────────┤
│  Search/Memory Layer            │  SearXNG search, RAG (future)
├─────────────────────────────────┤
│  Model Layer                    │  LLM wrappers + error handling
├─────────────────────────────────┤
│  Data Layer                     │  Vector stores (future)
└─────────────────────────────────┘
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

- ✅ **Web Search Integration** - SearXNG-powered search with source display
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
