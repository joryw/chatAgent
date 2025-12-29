# Quick Start Guide

This guide will help you get the AI Agent up and running in 5 minutes.

## Step 1: Prerequisites

Before starting, make sure you have:

- Python 3.11 or higher installed
- An API key from at least one provider:
  - [OpenAI API Key](https://platform.openai.com/api-keys)
  - [DeepSeek API Key](https://platform.deepseek.com/)
  - [Anthropic API Key](https://console.anthropic.com/)

## Step 2: Installation

### Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd chatAgent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configuration

Create a `.env` file in the project root:

```bash
# Minimum configuration (OpenAI only)
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4
DEFAULT_PROVIDER=openai
```

**Important**: Replace `sk-your-actual-api-key-here` with your real API key!

### Optional: Configure Multiple Providers

If you want to use multiple providers:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4

# DeepSeek (cost-effective alternative)
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MODEL_VARIANT=deepseek-chat  # or deepseek-reasoner for reasoning model
DEEPSEEK_MAX_TOKENS=2000  # Max output: 8K (chat) / 64K (reasoner). Context: 128K

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Choose default provider
DEFAULT_PROVIDER=openai
```

## Step 4: Run the Application

Start the Chainlit interface:

```bash
chainlit run app.py -w
```

The application will start on `http://localhost:8000`. Your browser should open automatically.

## Step 5: Start Chatting!

### Basic Usage

1. Type your message in the chat input at the bottom
2. Press Enter or click Send
3. The AI will respond with:
   - The generated response
   - Metadata (tokens used, model name, etc.)

### Try These Commands

Type these commands in the chat:

```
/help          # Show all available commands
/config        # View current model settings
/switch deepseek   # Switch to DeepSeek (if configured)
/reset         # Clear conversation history
```

## Example Conversations

### Simple Question
```
You: What is the capital of France?
AI: The capital of France is Paris.
```

### Switch Providers Mid-Conversation
```
You: /switch deepseek
System: ✅ Switched to deepseek
You: Tell me a joke
AI: [DeepSeek response]
```

### Using DeepSeek Reasoner Model

**Via UI Settings Panel:**
1. Click ⚙️ icon in top-right corner
2. Select "deepseek-reasoner" from "🤖 DeepSeek 模型" dropdown
3. Ask a complex question

**Example with Reasoning Display:**
```
You: Solve this logic puzzle: If all roses are flowers, and some flowers fade quickly, can we conclude that some roses fade quickly?

AI: 
💭 思考中... (streaming)
[Thinking process displays here in real-time]
- Analyzing the logical structure...
- Identifying the premises...
- Checking for valid inference...

💡 思考过程 (collapsed after answer starts)

[Final Answer]
No, we cannot conclude that some roses fade quickly from the given premises...
```

## Troubleshooting

### "Invalid API key" Error

**Problem**: The API key is not valid or not set correctly.

**Solution**:
1. Check your `.env` file exists in the project root
2. Verify the API key is correct and complete
3. Make sure there are no extra spaces or quotes around the key

### "No model providers configured" Error

**Problem**: No valid API keys found.

**Solution**:
1. Make sure `.env` file exists
2. At least one provider must have a valid API key
3. Check that keys don't start with placeholder text like "sk-your-"

### Module Import Errors

**Problem**: Python can't find the installed packages.

**Solution**:
1. Make sure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.11+)

## Next Steps

Now that you have the basic setup working, you can:

1. **Customize Model Parameters**: Edit temperature, max_tokens in `.env`
2. **Try Different Models**: Switch between providers using `/switch`
3. **Explore Advanced Features**: See [Configuration Guide](./CONFIGURATION.md)
4. **Integrate into Your App**: See [Developer Guide](../README.md#development)

## Getting Help

- Check the [README](../README.md) for detailed documentation
- Review [Configuration Guide](./CONFIGURATION.md) for all settings
- Open an issue on GitHub for bugs or questions

Happy chatting! 🚀

