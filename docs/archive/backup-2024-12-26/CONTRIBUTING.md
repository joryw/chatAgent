# Contributing to AI Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Collect information about the bug:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment (Python version, OS, etc.)
   - Logs/error messages

Create an issue with:
- Clear, descriptive title
- Detailed description
- Code samples if applicable
- Screenshots if relevant

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues:
1. Use a clear, descriptive title
2. Provide detailed description of enhancement
3. Explain why this enhancement would be useful
4. Include examples of how it would work

### Pull Requests

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/chatAgent.git
   cd chatAgent
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow the code style guide
   - Add tests if applicable
   - Update documentation

4. **Test Your Changes**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Test manually with Chainlit
   chainlit run app.py
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
   
   Follow commit message format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a Pull Request on GitHub.

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- API key for at least one LLM provider

### Setup

```bash
# Clone repository
git clone https://github.com/your-username/chatAgent.git
cd chatAgent

# Run setup script
./setup.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys
```

### Running Tests

Currently, testing is manual through the Chainlit interface:

```bash
chainlit run app.py -w
```

Test checklist:
- [ ] Basic conversation works
- [ ] Model switching works
- [ ] Commands work (/help, /config, /switch, /reset)
- [ ] Error handling works (test with invalid inputs)
- [ ] Token counting displays correctly
- [ ] Different providers work (if configured)

## Code Style Guide

### Python Style

Follow PEP 8 with these specifics:

- **Line Length**: 88 characters (black default)
- **Quotes**: Double quotes for strings
- **Imports**: Grouped and sorted (use isort)
- **Type Hints**: Required for function signatures
- **Docstrings**: Required for all public functions/classes

### Example

```python
def process_message(user_input: str, context: dict) -> str:
    """Process user message and generate response.
    
    Args:
        user_input: The user's message text
        context: Conversation context dictionary
        
    Returns:
        Generated response string
        
    Raises:
        ValueError: If input is invalid
    """
    # Implementation
    pass
```

### Naming Conventions

- **Functions/methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### File Organization

```python
# 1. Standard library imports
import os
from typing import Optional

# 2. Third-party imports
from dotenv import load_dotenv
import chainlit as cl

# 3. Local imports
from src.config import ModelConfig
from src.models import get_model_wrapper
```

## Project Structure

```
chatAgent/
├── src/
│   ├── config/          # Configuration management
│   ├── models/          # Model wrappers
│   └── prompts/         # Prompt templates
├── docs/                # Documentation
├── tests/               # Tests (future)
├── app.py               # Main application
└── requirements.txt     # Dependencies
```

## Adding a New Model Provider

To add support for a new LLM provider:

1. **Create Wrapper**
   ```python
   # src/models/newprovider_wrapper.py
   from .base import BaseModelWrapper, ModelResponse
   
   class NewProviderWrapper(BaseModelWrapper):
       def __init__(self, config: ModelConfig):
           super().__init__(config)
           # Initialize provider client
       
       async def generate(self, prompt: str, **kwargs) -> ModelResponse:
           # Implement generation
           pass
       
       def count_tokens(self, text: str) -> int:
           # Implement token counting
           pass
   ```

2. **Update Configuration**
   ```python
   # src/config/model_config.py
   class ModelProvider(str, Enum):
       OPENAI = "openai"
       ANTHROPIC = "anthropic"
       DEEPSEEK = "deepseek"
       NEWPROVIDER = "newprovider"  # Add this
   ```

3. **Update Factory**
   ```python
   # src/models/factory.py
   from .newprovider_wrapper import NewProviderWrapper
   
   def get_model_wrapper(provider: Optional[str] = None) -> BaseModelWrapper:
       # ...
       elif config.provider == ModelProvider.NEWPROVIDER:
           return NewProviderWrapper(config)
   ```

4. **Update Documentation**
   - Add configuration example to README.md
   - Add section to docs/CONFIGURATION.md
   - Update env.example

5. **Test**
   - Manually test with Chainlit interface
   - Test error handling
   - Test switching between providers

## Documentation

### When to Update Documentation

Update docs when you:
- Add new features
- Change configuration options
- Add new dependencies
- Change API/interface
- Fix bugs that affect usage

### Documentation Files

- **README.md**: Main documentation, quick start, features
- **docs/QUICK_START.md**: Step-by-step setup guide
- **docs/CONFIGURATION.md**: Detailed configuration guide
- **Code comments**: Complex logic, non-obvious decisions
- **Docstrings**: All public functions and classes

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Read documentation in docs/

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🚀

