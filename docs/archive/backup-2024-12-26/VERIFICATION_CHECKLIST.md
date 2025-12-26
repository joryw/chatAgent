# Verification Checklist

Use this checklist to verify that the Model Invocation feature is working correctly.

## ✅ Pre-Deployment Verification

### 1. Installation & Setup

- [ ] Python 3.11+ is installed
- [ ] Virtual environment created successfully
- [ ] All dependencies installed without errors
- [ ] `.env` file created from `env.example`
- [ ] At least one API key configured
- [ ] API key is valid (not placeholder text)

**Commands:**
```bash
python3 --version  # Should be 3.11+
./setup.sh         # Should complete without errors
```

### 2. Configuration Validation

- [ ] `.env` file exists and is readable
- [ ] API keys are properly formatted
- [ ] `DEFAULT_PROVIDER` is set correctly
- [ ] Model names are valid
- [ ] Temperature values are in range (0.0-2.0)
- [ ] Max tokens are positive integers

**Test:**
```bash
# Check .env file
cat .env | grep -v "^#" | grep "API_KEY"

# Should show your API keys (not placeholder values)
```

### 3. Application Startup

- [ ] Application starts without errors
- [ ] Chainlit UI loads at http://localhost:8000
- [ ] Welcome message displays
- [ ] Current configuration is shown
- [ ] Available providers are listed

**Commands:**
```bash
./run.sh
# Or:
source venv/bin/activate
chainlit run app.py -w
```

**Expected Output:**
```
🤖 Welcome to AI Agent Chat!

Current Model: gpt-4
Provider: openai
Temperature: 0.7
Max Tokens: 2000

Available Providers: openai, deepseek

You can start chatting now!
```

## ✅ Functional Testing

### 4. Basic Conversation

- [ ] Can send a message
- [ ] Receives a response
- [ ] Response is coherent and relevant
- [ ] Token count is displayed
- [ ] Model name is shown
- [ ] No error messages

**Test Cases:**
```
Test 1: Simple question
Input: "What is 2+2?"
Expected: Correct answer (4)

Test 2: Longer response
Input: "Explain machine learning in 3 sentences"
Expected: Coherent 3-sentence explanation

Test 3: Code generation
Input: "Write a hello world in Python"
Expected: Valid Python code
```

### 5. Command System

**Test `/help` command:**
- [ ] Command executes without error
- [ ] Shows all available commands
- [ ] Formatting is correct

**Test `/config` command:**
- [ ] Shows current provider
- [ ] Shows model name
- [ ] Shows all parameters
- [ ] Lists available providers

**Test `/reset` command:**
- [ ] Executes successfully
- [ ] Shows confirmation message
- [ ] Conversation history is cleared
- [ ] Next message starts fresh

**Test `/switch` command:**
- [ ] Without argument shows error with help
- [ ] With invalid provider shows error
- [ ] With valid provider switches successfully
- [ ] Shows new configuration
- [ ] Subsequent messages use new provider

### 6. Provider Switching (if multiple configured)

**Test OpenAI:**
- [ ] `/switch openai` works
- [ ] Can send message
- [ ] Response uses OpenAI model
- [ ] Metadata shows correct model

**Test DeepSeek:**
- [ ] `/switch deepseek` works
- [ ] Can send message
- [ ] Response uses DeepSeek model
- [ ] Metadata shows correct model

**Test Anthropic (if configured):**
- [ ] `/switch anthropic` works
- [ ] Can send message
- [ ] Response uses Claude model
- [ ] Metadata shows correct model

### 7. Error Handling

**Test invalid API key:**
- [ ] Edit `.env` with invalid key
- [ ] Restart application
- [ ] Attempt to send message
- [ ] Shows clear error message
- [ ] Suggests how to fix

**Test network issues:**
- [ ] Disconnect network (or use invalid base URL)
- [ ] Attempt to send message
- [ ] Shows timeout or network error
- [ ] Error message is helpful

**Test rate limiting (if possible):**
- [ ] Send many rapid requests
- [ ] System handles rate limit gracefully
- [ ] Automatic retry works
- [ ] Eventually succeeds or shows clear error

### 8. Token Management

**Test token counting:**
- [ ] Send short message
- [ ] Token count is reasonable (< 50)
- [ ] Send long message
- [ ] Token count is higher
- [ ] Prompt and completion tokens shown separately

**Test context validation:**
- [ ] Send very long message (near limit)
- [ ] System warns about context length
- [ ] Still processes request
- [ ] Or shows clear error if too long

### 9. Multi-Turn Conversation

**Test conversation flow:**
- [ ] Send first message
- [ ] Send follow-up question
- [ ] Response is contextually relevant
- [ ] Send third message
- [ ] Conversation maintains context

**Test history reset:**
- [ ] Have multi-turn conversation
- [ ] Use `/reset`
- [ ] Send message
- [ ] Response doesn't reference previous context

### 10. Performance

**Test response times:**
- [ ] Simple query responds in < 10 seconds
- [ ] Complex query responds in < 30 seconds
- [ ] No hanging or freezing
- [ ] UI remains responsive

**Test concurrent operations:**
- [ ] Send message
- [ ] While processing, UI is responsive
- [ ] Can view previous messages
- [ ] Processing indicator shows

## ✅ Code Quality

### 11. Code Structure

- [ ] All files follow PEP 8 style
- [ ] Type hints present on functions
- [ ] Docstrings present on public functions
- [ ] No linter errors
- [ ] Imports are organized

**Commands:**
```bash
# Check for linter errors (if tools installed)
black --check src/ app.py
isort --check src/ app.py
mypy src/ app.py
```

### 12. Configuration

- [ ] `.env.example` is complete
- [ ] `.gitignore` includes `.env`
- [ ] No API keys in git history
- [ ] Configuration is well-documented
- [ ] Validation catches invalid values

### 13. Error Messages

- [ ] All errors have clear messages
- [ ] Errors suggest solutions
- [ ] No stack traces shown to users
- [ ] Errors are logged appropriately

## ✅ Documentation

### 14. README

- [ ] Installation instructions are clear
- [ ] Quick start works as described
- [ ] All features are documented
- [ ] Examples are accurate
- [ ] Troubleshooting section is helpful

### 15. Additional Docs

- [ ] Quick Start guide is accurate
- [ ] Configuration guide is complete
- [ ] Contributing guidelines are clear
- [ ] Usage examples work
- [ ] All links work

### 16. Code Documentation

- [ ] All public functions have docstrings
- [ ] Complex logic has comments
- [ ] Type hints are accurate
- [ ] Examples in docstrings work

## ✅ Security

### 17. API Key Security

- [ ] API keys in `.env` only
- [ ] `.env` in `.gitignore`
- [ ] No keys in code
- [ ] No keys in logs
- [ ] `.env.example` has placeholder values

### 18. Input Validation

- [ ] User input is validated
- [ ] Configuration is validated
- [ ] No code injection possible
- [ ] Error messages don't leak sensitive info

## ✅ Deployment Readiness

### 19. Dependencies

- [ ] `requirements.txt` is complete
- [ ] All versions are specified
- [ ] No conflicting dependencies
- [ ] All packages install successfully

### 20. Scripts

- [ ] `setup.sh` works correctly
- [ ] `run.sh` works correctly
- [ ] Scripts have proper permissions
- [ ] Scripts handle errors gracefully

### 21. Environment

- [ ] Works on macOS
- [ ] Works on Linux
- [ ] Works on Windows (WSL)
- [ ] Python 3.11+ requirement met

## ✅ Specification Compliance

### 22. Requirements Coverage

Review `openspec/changes/add-model-invocation/specs/model-invocation/spec.md`:

- [ ] All "Model Provider Support" requirements met
- [ ] All "Model Configuration" requirements met
- [ ] All "Prompt Management" requirements met
- [ ] All "Error Handling" requirements met
- [ ] All "Response Processing" requirements met
- [ ] All "LangChain Integration" requirements met
- [ ] All "Chainlit Interface" requirements met

### 23. Tasks Completion

Review `openspec/changes/add-model-invocation/tasks.md`:

- [ ] All section 1 tasks (Model Configuration) completed
- [ ] All section 2 tasks (Model Invocation Layer) completed
- [ ] All section 3 tasks (Prompt Management) completed
- [ ] All section 4 tasks (Error Handling) completed
- [ ] All section 5 tasks (Chainlit Integration) completed
- [ ] All section 6 tasks (Interface Testing) completed
- [ ] All section 7 tasks (Documentation) completed

## 📋 Sign-Off

### Pre-Deployment

- [ ] All critical tests pass
- [ ] Documentation is complete
- [ ] No known critical bugs
- [ ] Code is reviewed
- [ ] Ready for user testing

### Post-Deployment

- [ ] Monitor for errors
- [ ] Collect user feedback
- [ ] Track token usage
- [ ] Monitor API costs
- [ ] Plan next iteration

## 🐛 Known Issues

Document any known issues here:

1. **Issue**: [Description]
   - **Impact**: [Low/Medium/High]
   - **Workaround**: [If available]
   - **Fix planned**: [Yes/No/Version]

2. **Issue**: Token counting for Anthropic is approximate
   - **Impact**: Low (doesn't affect functionality)
   - **Workaround**: Use character-based estimation
   - **Fix planned**: When official tokenizer available

## 📝 Notes

Add any additional notes or observations:

- Performance benchmarks
- Cost analysis
- User feedback
- Improvement ideas

## ✅ Final Checklist

Before marking as complete:

- [ ] All critical tests pass
- [ ] Documentation reviewed
- [ ] Code reviewed
- [ ] Security checked
- [ ] Ready for production

**Verified by**: _______________  
**Date**: _______________  
**Version**: 0.1.0  
**Status**: ☐ Ready ☐ Needs Work ☐ Blocked

---

## Quick Test Script

Run this quick test to verify basic functionality:

```bash
# 1. Setup
./setup.sh

# 2. Configure
cp env.example .env
# Edit .env with your API key

# 3. Run
./run.sh

# 4. Test in browser (http://localhost:8000)
# - Send: "Hello"
# - Send: "/config"
# - Send: "/help"
# - Send: "/reset"
# - Send: "What is 2+2?"

# 5. If multiple providers configured:
# - Send: "/switch deepseek"
# - Send: "Test message"
# - Send: "/switch openai"

# 6. Stop server (Ctrl+C)
```

If all tests pass, the system is ready! 🚀

