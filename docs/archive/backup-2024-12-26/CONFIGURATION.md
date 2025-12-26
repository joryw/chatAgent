# Configuration Guide

Complete guide to configuring the AI Agent for different use cases.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Model Parameters](#model-parameters)
- [Provider-Specific Configuration](#provider-specific-configuration)
- [Advanced Settings](#advanced-settings)
- [Best Practices](#best-practices)

## Environment Variables

All configuration is done through environment variables in a `.env` file.

### Required Variables

At least one provider must be configured:

```bash
# Option 1: OpenAI (recommended for beginners)
OPENAI_API_KEY=sk-your-key-here
DEFAULT_PROVIDER=openai

# OR Option 2: DeepSeek (cost-effective)
DEEPSEEK_API_KEY=sk-your-key-here
DEFAULT_PROVIDER=deepseek

# OR Option 3: Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-your-key-here
DEFAULT_PROVIDER=anthropic
```

### Optional Variables

```bash
# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

## Model Parameters

### Temperature

Controls randomness in responses.

```bash
OPENAI_TEMPERATURE=0.7
DEEPSEEK_TEMPERATURE=0.7
ANTHROPIC_TEMPERATURE=0.7
```

**Range**: 0.0 to 2.0

- **0.0-0.3**: Very deterministic, focused, good for:
  - Factual questions
  - Code generation
  - Data extraction
  
- **0.4-0.7**: Balanced, default for:
  - General conversation
  - Creative writing
  - Problem solving
  
- **0.8-2.0**: Very creative, good for:
  - Brainstorming
  - Fiction writing
  - Artistic content

**Example Use Cases**:

```bash
# For code generation
OPENAI_TEMPERATURE=0.2

# For creative writing
OPENAI_TEMPERATURE=0.9

# For balanced conversation
OPENAI_TEMPERATURE=0.7
```

### Max Tokens

Maximum length of generated response.

```bash
OPENAI_MAX_TOKENS=2000
DEEPSEEK_MAX_TOKENS=2000
ANTHROPIC_MAX_TOKENS=2000
```

**Guidelines**:
- 1 token ≈ 4 characters in English
- 1 token ≈ 0.75 words in English

**Example Settings**:

```bash
# Short responses (tweets, summaries)
MAX_TOKENS=150

# Medium responses (email, explanations)
MAX_TOKENS=500

# Long responses (articles, detailed analysis)
MAX_TOKENS=2000

# Very long responses (be mindful of costs!)
MAX_TOKENS=4000
```

### Top P

Nucleus sampling parameter (alternative to temperature).

```bash
# Default: 1.0 (disabled)
# Usually not needed if using temperature
```

**Range**: 0.0 to 1.0

- **1.0**: Consider all tokens (default)
- **0.1**: Very focused, only most likely tokens
- **0.5**: Moderate diversity

**Note**: Generally, use either temperature OR top_p, not both.

### Timeout

Request timeout in seconds.

```bash
# Default: 30 seconds
TIMEOUT=30

# For longer responses
TIMEOUT=60

# For quick responses
TIMEOUT=15
```

## Provider-Specific Configuration

### OpenAI

```bash
# API Key (required)
OPENAI_API_KEY=sk-proj-...

# Model selection
OPENAI_MODEL=gpt-4              # Most capable, slower, more expensive
# OPENAI_MODEL=gpt-4-turbo      # Faster GPT-4
# OPENAI_MODEL=gpt-3.5-turbo    # Faster, cheaper, less capable

# Parameters
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

**Available Models**:
- `gpt-4`: Most capable, best reasoning
- `gpt-4-turbo`: Faster, cheaper GPT-4
- `gpt-3.5-turbo`: Fast, affordable, good for simple tasks

**Costs** (approximate, as of 2024):
- GPT-4: $0.03/1K prompt tokens, $0.06/1K completion
- GPT-3.5-turbo: $0.0015/1K prompt tokens, $0.002/1K completion

### DeepSeek

```bash
# API Key (required)
DEEPSEEK_API_KEY=sk-...

# Base URL
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Model selection
DEEPSEEK_MODEL=deepseek-chat    # Main chat model
# DEEPSEEK_MODEL=deepseek-coder # Specialized for code

# Parameters
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=2000
```

**Features**:
- OpenAI-compatible API
- Very cost-effective
- Good performance for general tasks
- Excellent for code generation

**Best For**:
- Development and testing
- High-volume applications
- Code-related tasks

### Anthropic (Claude)

```bash
# API Key (required)
ANTHROPIC_API_KEY=sk-ant-...

# Model selection
ANTHROPIC_MODEL=claude-3-sonnet-20240229   # Balanced
# ANTHROPIC_MODEL=claude-3-opus-20240229   # Most capable
# ANTHROPIC_MODEL=claude-3-haiku-20240307  # Fastest, cheapest

# Parameters
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_MAX_TOKENS=2000
```

**Model Tiers**:
- **Haiku**: Fast, affordable, simple tasks
- **Sonnet**: Balanced performance and speed
- **Opus**: Maximum capability, complex reasoning

**Strengths**:
- Long context windows (200K tokens)
- Strong reasoning capabilities
- Excellent at following instructions
- Good at refusing harmful requests

## Advanced Settings

### Multiple Provider Setup

Configure all providers to switch between them:

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4

# DeepSeek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Default provider
DEFAULT_PROVIDER=deepseek
```

Then switch during conversation:
```
/switch openai
/switch deepseek
/switch anthropic
```

### Environment-Specific Configuration

Create different `.env` files for different environments:

```bash
# .env.development
OPENAI_API_KEY=sk-test-...
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.8
LOG_LEVEL=DEBUG

# .env.production
OPENAI_API_KEY=sk-prod-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
LOG_LEVEL=INFO
```

Load with:
```bash
# Development
cp .env.development .env
chainlit run app.py

# Production
cp .env.production .env
chainlit run app.py
```

## Best Practices

### 1. API Key Security

**DO**:
- ✅ Store API keys in `.env` file
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment variables in production
- ✅ Rotate keys regularly

**DON'T**:
- ❌ Commit API keys to version control
- ❌ Share keys in chat/email
- ❌ Use production keys in development
- ❌ Hardcode keys in source code

### 2. Cost Optimization

**Tips for Reducing Costs**:

1. **Use Cheaper Models for Simple Tasks**
   ```bash
   # Instead of:
   OPENAI_MODEL=gpt-4
   
   # Use:
   OPENAI_MODEL=gpt-3.5-turbo  # 20x cheaper!
   ```

2. **Reduce Max Tokens**
   ```bash
   # Instead of:
   OPENAI_MAX_TOKENS=4000
   
   # Use:
   OPENAI_MAX_TOKENS=500  # Usually sufficient
   ```

3. **Consider DeepSeek**
   ```bash
   # Much more cost-effective than OpenAI
   DEFAULT_PROVIDER=deepseek
   ```

4. **Clear History Regularly**
   ```
   /reset  # Clear conversation history to reduce prompt size
   ```

### 3. Performance Optimization

**For Faster Responses**:

```bash
# Use faster models
OPENAI_MODEL=gpt-3.5-turbo  # Much faster than GPT-4

# Reduce max tokens
OPENAI_MAX_TOKENS=500

# Lower timeout
TIMEOUT=15
```

**For Higher Quality**:

```bash
# Use more capable models
OPENAI_MODEL=gpt-4
ANTHROPIC_MODEL=claude-3-opus-20240229

# Allow more tokens
OPENAI_MAX_TOKENS=2000

# Lower temperature for focus
OPENAI_TEMPERATURE=0.3
```

### 4. Error Handling

The system automatically handles:
- Rate limiting (HTTP 429) - retries with backoff
- Network timeouts - retries up to 3 times
- Invalid requests - fails immediately with clear error

**Configuration for Reliability**:

```bash
# Increase timeout for unreliable networks
TIMEOUT=60

# Use stable providers
DEFAULT_PROVIDER=openai  # Generally most reliable
```

### 5. Testing Configuration

Test your configuration:

```bash
# 1. Start the app
chainlit run app.py

# 2. Check config
/config

# 3. Try a simple query
Hello, can you hear me?

# 4. Test provider switching (if multiple configured)
/switch deepseek
```

## Configuration Examples

### Example 1: Development Setup (Low Cost)

```bash
# Use DeepSeek for cost savings
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=500

DEFAULT_PROVIDER=deepseek
LOG_LEVEL=DEBUG
```

### Example 2: Production Setup (High Quality)

```bash
# Use GPT-4 for production
OPENAI_API_KEY=sk-prod-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.5  # More focused
OPENAI_MAX_TOKENS=1000

DEFAULT_PROVIDER=openai
LOG_LEVEL=INFO
```

### Example 3: Multi-Provider Setup

```bash
# Primary: DeepSeek (cost-effective)
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat

# Fallback: OpenAI (when need high quality)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Alternative: Anthropic (for long context)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229

DEFAULT_PROVIDER=deepseek
```

## Troubleshooting Configuration

### Issue: API Key Not Working

**Check**:
1. Key is complete (no truncation)
2. No extra spaces or quotes
3. Correct provider (OpenAI keys start with `sk-`, Anthropic with `sk-ant-`)

### Issue: Unexpected Responses

**Check**:
1. Temperature setting (try lowering to 0.3-0.5)
2. Model selection (verify you're using intended model)
3. System message (check if custom prompts are affecting behavior)

### Issue: Slow Responses

**Check**:
1. Model selection (GPT-4 is slower than GPT-3.5)
2. Max tokens (lower values = faster responses)
3. Network connection
4. Provider status

## Getting Help

If you have configuration issues:

1. Check the [Quick Start Guide](./QUICK_START.md)
2. Review [README.md](../README.md)
3. Enable debug logging: `LOG_LEVEL=DEBUG`
4. Open an issue with your configuration (redact API keys!)

