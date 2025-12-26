# AI Agent with Model Invocation

A conversational AI agent with support for multiple LLM providers (OpenAI, Anthropic, DeepSeek) built with LangChain and Chainlit.

## Features

- 🤖 **Multi-Provider Support**: Seamlessly switch between OpenAI, Anthropic, and DeepSeek models
- 💬 **Interactive Chat Interface**: Beautiful Chainlit UI for testing and conversation
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
```

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
│   │   └── model_config.py  # Model settings and validation
│   ├── models/              # Model wrappers
│   │   ├── __init__.py
│   │   ├── base.py          # Base wrapper interface
│   │   ├── openai_wrapper.py
│   │   ├── deepseek_wrapper.py
│   │   ├── anthropic_wrapper.py
│   │   └── factory.py       # Model wrapper factory
│   └── prompts/             # Prompt management
│       ├── __init__.py
│       └── templates.py     # Prompt templates and utilities
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
│  Search/Memory Layer            │  RAG, memory (future)
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

## Future Enhancements

- [ ] RAG (Retrieval Augmented Generation) support
- [ ] Long-term conversation memory
- [ ] Multi-agent collaboration
- [ ] Custom tool/skill integration
- [ ] Streaming responses
- [ ] Conversation export/import
- [ ] Advanced prompt engineering features

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please follow the existing code style and add tests for new features.

## Support

For issues and questions, please open an issue on the GitHub repository.
