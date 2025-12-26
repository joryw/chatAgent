# Usage Examples

Real-world examples of using the AI Agent with different providers and configurations.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Provider Switching](#provider-switching)
- [Configuration Management](#configuration-management)
- [Advanced Scenarios](#advanced-scenarios)
- [Troubleshooting Examples](#troubleshooting-examples)

## Basic Usage

### Example 1: Simple Question

```
You: What is the capital of France?

AI: The capital of France is Paris. It's located in the north-central 
part of the country and is not only the capital but also the largest 
city in France, known for its art, culture, and history.

---
📊 Response Metadata:
- Model: gpt-4
- Tokens Used: 52 (prompt: 18, completion: 34)
- Finish Reason: stop
```

### Example 2: Code Generation

```
You: Write a Python function to calculate factorial

AI: Here's a Python function to calculate factorial:

```python
def factorial(n):
    """Calculate factorial of n.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

# Example usage
print(factorial(5))  # Output: 120
```

This function uses recursion. For large numbers, you might want to use 
an iterative approach to avoid stack overflow.

---
📊 Response Metadata:
- Model: gpt-4
- Tokens Used: 187 (prompt: 15, completion: 172)
- Finish Reason: stop
```

### Example 3: Creative Writing

```
You: Write a haiku about programming

AI: Code flows like water,
    Bugs dance in moonlit debug—
    Coffee fuels the night.

---
📊 Response Metadata:
- Model: gpt-4
- Tokens Used: 45 (prompt: 12, completion: 33)
- Finish Reason: stop
```

## Provider Switching

### Example 4: Comparing Providers

**Using OpenAI GPT-4:**
```
You: Explain quantum computing in one sentence

AI (GPT-4): Quantum computing harnesses the principles of quantum 
mechanics, such as superposition and entanglement, to perform 
computations exponentially faster than classical computers for 
certain types of problems.

---
📊 Response Metadata:
- Model: gpt-4
- Tokens Used: 58
```

**Switch to DeepSeek:**
```
You: /switch deepseek

System: ✅ Switched to deepseek

Model: deepseek-chat
Temperature: 0.7
Max Tokens: 2000

Conversation history has been cleared.
```

**Same question with DeepSeek:**
```
You: Explain quantum computing in one sentence

AI (DeepSeek): Quantum computing uses quantum bits (qubits) that can 
exist in multiple states simultaneously, enabling parallel processing 
of vast amounts of data for solving complex problems much faster than 
classical computers.

---
📊 Response Metadata:
- Model: deepseek-chat
- Tokens Used: 62
```

### Example 5: Provider for Different Tasks

**Use GPT-4 for complex reasoning:**
```
You: /switch openai

You: Analyze the ethical implications of AI in healthcare

AI: [Detailed, nuanced analysis with multiple perspectives...]
```

**Use DeepSeek for code:**
```
You: /switch deepseek

You: Optimize this Python code for performance
[code snippet]

AI: [Code optimization with explanations...]
```

**Use Claude for long-form content:**
```
You: /switch anthropic

You: Write a comprehensive guide to machine learning

AI: [Detailed, well-structured guide...]
```

## Configuration Management

### Example 6: Viewing Configuration

```
You: /config

System: # ⚙️ Current Configuration

**Provider:** openai
**Model:** gpt-4
**Temperature:** 0.7
**Max Tokens:** 2000
**Top P:** 1.0
**Timeout:** 30s

**Available Providers:** openai, deepseek
```

### Example 7: Checking Available Providers

```
You: /help

System: # 📖 Available Commands

- `/switch <provider>` - Switch to a different model provider 
  (openai, anthropic, deepseek)
- `/config` - View current model configuration
- `/reset` - Clear conversation history
- `/help` - Show this help message

**Example:**
```
/switch deepseek
```
```

### Example 8: Resetting Conversation

```
You: /reset

System: ✅ Conversation history cleared.

You: [Start fresh conversation...]
```

## Advanced Scenarios

### Example 9: Multi-Turn Conversation

```
You: What is machine learning?

AI: Machine learning is a subset of artificial intelligence that 
enables systems to learn and improve from experience without being 
explicitly programmed...

You: Can you give me an example?

AI: Sure! A common example is email spam filtering. The system learns 
from thousands of examples of spam and legitimate emails...

You: How does it learn?

AI: It learns through algorithms that identify patterns in the data. 
For spam detection, it might learn that emails with certain words...
```

### Example 10: Cost-Effective Development

**Development Setup (using DeepSeek):**
```bash
# .env configuration
DEFAULT_PROVIDER=deepseek
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.7
```

```
You: [Testing various features with DeepSeek]
AI: [Responses at fraction of GPT-4 cost]

# When need high-quality output:
You: /switch openai
AI: [Switch to GPT-4 for critical tasks]
```

### Example 11: Temperature Comparison

**Low Temperature (0.2) - Focused:**
```bash
# .env
OPENAI_TEMPERATURE=0.2
```

```
You: What is 2+2?
AI: 4
```

**High Temperature (0.9) - Creative:**
```bash
# .env
OPENAI_TEMPERATURE=0.9
```

```
You: Write a creative story about a robot
AI: [Highly creative, varied response with unexpected elements]
```

### Example 12: Token Management

```
You: [Very long prompt with detailed context...]

System: 🤔 Thinking...

AI: [Response]

---
📊 Response Metadata:
- Model: gpt-4
- Tokens Used: 1847 (prompt: 1234, completion: 613)
- Finish Reason: stop

⚠️ Note: This conversation used significant tokens. Consider using 
/reset to clear history if responses become slow or expensive.
```

## Troubleshooting Examples

### Example 13: Invalid API Key

```
You: Hello

System: ❌ Error generating response: Authentication failed. 
Invalid API key provided.

Please check your .env file and ensure:
1. OPENAI_API_KEY is set correctly
2. The key is valid and active
3. There are no extra spaces or quotes

Try again after updating your configuration.
```

### Example 14: Provider Not Configured

```
You: /switch anthropic

System: ⚠️ Provider 'anthropic' not available or not configured.

Available providers: openai, deepseek

To add Anthropic:
1. Get API key from https://console.anthropic.com/
2. Add to .env: ANTHROPIC_API_KEY=sk-ant-your-key-here
3. Restart the application
```

### Example 15: Rate Limiting

```
You: [Multiple rapid requests...]

System: 🤔 Thinking...

[Automatic retry with backoff]

AI: [Response after retry]

Note: Rate limit encountered. The system automatically retried your 
request. If this happens frequently, consider:
- Reducing request frequency
- Upgrading your API plan
- Using a different provider
```

### Example 16: Network Timeout

```
You: [Complex query...]

System: 🤔 Thinking...

[After 30 seconds]

System: ❌ Error generating response: Request timeout after 30 seconds.

This might be due to:
- Network connectivity issues
- Provider service issues
- Very complex query requiring long processing

Try:
1. Check your internet connection
2. Simplify your query
3. Try again in a moment
4. Use /switch to try a different provider
```

## Real-World Use Cases

### Use Case 1: Code Review Assistant

```
You: /switch openai

You: Review this Python code for potential issues:

def process_data(data):
    result = []
    for i in range(len(data)):
        result.append(data[i] * 2)
    return result

AI: Here are some suggestions for improving this code:

1. **Use enumerate or direct iteration**: Instead of `range(len(data))`, 
   you can iterate directly:
   ```python
   for item in data:
       result.append(item * 2)
   ```

2. **Use list comprehension**: More Pythonic and efficient:
   ```python
   def process_data(data):
       return [item * 2 for item in data]
   ```

3. **Add type hints and docstring**:
   ```python
   def process_data(data: list[int]) -> list[int]:
       """Double each element in the data list."""
       return [item * 2 for item in data]
   ```

4. **Consider using map()** for functional approach:
   ```python
   def process_data(data):
       return list(map(lambda x: x * 2, data))
   ```

The list comprehension version is typically preferred for readability 
and performance.
```

### Use Case 2: Learning Assistant

```
You: I'm learning Python. Can you explain list comprehensions?

AI: List comprehensions provide a concise way to create lists in Python.

**Basic Syntax:**
```python
[expression for item in iterable if condition]
```

**Example 1 - Simple transformation:**
```python
# Traditional way
squares = []
for x in range(10):
    squares.append(x**2)

# List comprehension
squares = [x**2 for x in range(10)]
```

**Example 2 - With condition:**
```python
# Only even numbers
evens = [x for x in range(10) if x % 2 == 0]
# Result: [0, 2, 4, 6, 8]
```

**Example 3 - Nested:**
```python
# Flatten a 2D list
matrix = [[1, 2], [3, 4], [5, 6]]
flat = [num for row in matrix for num in row]
# Result: [1, 2, 3, 4, 5, 6]
```

**When to use:**
- ✅ Simple transformations
- ✅ Filtering lists
- ✅ When readability is maintained

**When NOT to use:**
- ❌ Complex logic (use regular loops)
- ❌ Side effects needed
- ❌ Multiple operations per item

Would you like to practice with some exercises?
```

### Use Case 3: Content Generation

```
You: /switch deepseek

You: Generate a product description for a smart water bottle

AI: **HydroSmart Pro - Your Intelligent Hydration Companion**

Stay perfectly hydrated with the HydroSmart Pro, the smart water 
bottle that tracks your water intake and reminds you to drink 
throughout the day.

**Key Features:**
• **Smart Tracking**: Built-in sensors monitor your daily water 
  consumption
• **LED Reminders**: Gentle light notifications when it's time to hydrate
• **App Integration**: Sync with iOS and Android for detailed insights
• **Temperature Display**: Know your drink's temperature at a glance
• **24-Hour Cold**: Vacuum insulation keeps drinks cold for 24 hours
• **Leak-Proof Design**: Secure lid for worry-free transport
• **Eco-Friendly**: BPA-free materials, reduce plastic waste

**Perfect For:**
- Fitness enthusiasts tracking hydration goals
- Busy professionals who forget to drink water
- Anyone committed to better health habits

**Specifications:**
- Capacity: 20 oz (600ml)
- Battery Life: 30 days per charge
- Material: Stainless steel with smart cap
- Available in: Midnight Black, Ocean Blue, Rose Gold

Transform your hydration routine with HydroSmart Pro. Because staying 
healthy starts with staying hydrated.

*Price: $49.99 | Free shipping on orders over $50*
```

## Tips for Best Results

### 1. Be Specific
```
❌ "Tell me about AI"
✅ "Explain how neural networks work in machine learning, focusing on 
    backpropagation"
```

### 2. Provide Context
```
❌ "Fix this code"
✅ "This Python function should sort a list, but it's returning None. 
    Can you help fix it? [code]"
```

### 3. Use Appropriate Provider
```
Complex reasoning → OpenAI GPT-4
Code generation → DeepSeek
Long content → Anthropic Claude
Quick tests → DeepSeek (cost-effective)
```

### 4. Manage Token Usage
```
# For long conversations:
You: /reset  # Clear history periodically

# For specific tasks:
You: [Focused, concise question]
```

### 5. Experiment with Temperature
```
# For factual information:
TEMPERATURE=0.3

# For creative content:
TEMPERATURE=0.9

# For balanced responses:
TEMPERATURE=0.7 (default)
```

## Next Steps

- Explore different providers for your use case
- Experiment with temperature settings
- Try different types of prompts
- Read [Configuration Guide](docs/CONFIGURATION.md) for advanced options
- Check [README](README.md) for more features

Happy chatting! 🚀

