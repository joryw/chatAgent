---
title: LangChain 迁移指南
title_en: LangChain Migration Guide
type: troubleshooting
created: 2024-12-28
updated: 2024-12-28
version: 1.0.0
tags: [langchain, migration, troubleshooting, dependencies]
lang: zh-CN
status: published
---

# LangChain 迁移指南

## 概述

本文档记录了将项目从旧版 LangChain (0.1.0) 迁移到新版 LangChain (1.2.0+) 和 LangGraph 的过程和解决方案。

## 问题背景

在尝试运行应用时遇到以下导入错误：

```python
ImportError: cannot import name 'ChatAnthropic' from 'langchain_anthropic'
ImportError: cannot import name 'AgentExecutor' from 'langchain.agents'
```

## 根本原因

LangChain 在 v0.2+ 版本进行了重大架构调整：

1. **分离核心包**: 功能被拆分到多个独立包
   - `langchain-core`: 核心抽象和接口
   - `langchain-community`: 社区集成
   - `langchain-openai`: OpenAI 集成
   - `langchain-anthropic`: Anthropic 集成
   - `langgraph`: Agent 和工作流（新增）

2. **Agent 架构变化**: 
   - 旧: `langchain.agents.AgentExecutor` + `create_react_agent()`
   - 新: `langgraph.prebuilt.create_react_agent()`

3. **API 变化**:
   - Agent 输入从 `{"input": "..."}` 改为 `{"messages": [HumanMessage(...)]}`
   - 返回值从字典改为包含消息列表的结构

## 解决方案

### 1. 更新依赖包版本

**更新前 (`requirements.txt`)**:
```ini
langchain==0.1.0
langchain-openai==0.0.2
langchain-anthropic==0.0.1
openai==1.6.1
anthropic==0.8.1
chainlit==1.0.0
```

**更新后 (`requirements.txt`)**:
```ini
langchain>=0.1.0
langchain-core>=0.1.0
langchain-community>=0.4.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0
langgraph>=1.0.0
openai>=1.6.1
anthropic>=0.8.1
chainlit>=1.0.0
```

**安装命令**:
```bash
pip install --upgrade -r requirements.txt
```

### 2. 更新 ReActAgent 导入

**旧代码 (`src/agents/react_agent.py`)**:
```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish
```

**新代码**:
```python
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import HumanMessage, AIMessage
```

### 3. 更新 Agent 创建逻辑

**旧代码**:
```python
self.prompt = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE)
self.agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=self.prompt)
self.agent_executor = AgentExecutor.from_agent_and_tools(
    agent=self.agent,
    tools=self.tools,
    verbose=self.config.verbose,
    max_iterations=self.config.max_iterations,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
)
```

**新代码**:
```python
# LangGraph 的 create_react_agent 内部处理 prompt
self.agent_executor = create_react_agent(
    model=self.llm,
    tools=self.tools,
)
```

### 4. 更新 Agent 调用方式

**旧代码**:
```python
result = await self.agent_executor.ainvoke({"input": user_input})
final_answer = result.get("output", "")
intermediate_steps = result.get("intermediate_steps", [])
```

**新代码**:
```python
result = await self.agent_executor.ainvoke(
    {"messages": [HumanMessage(content=user_input)]}
)
messages = result.get("messages", [])
final_message = messages[-1] if messages else None
final_answer = final_message.content if final_message else ""
```

### 5. 更新流式输出

**旧代码**:
```python
async for chunk in self.agent_executor.astream_log(...):
    # 解析 astream_log 的输出
    pass
```

**新代码**:
```python
async for event in self.agent_executor.astream(...):
    if "agent" in event:
        # Agent 思考
        pass
    elif "tools" in event:
        # 工具执行
        pass
```

### 6. 更新模型 Wrapper

确保所有模型 wrapper 实现 `get_langchain_llm()` 方法：

**AnthropicWrapper** (`src/models/anthropic_wrapper.py`):
```python
from langchain_anthropic import ChatAnthropic

def get_langchain_llm(self) -> BaseChatModel:
    """Returns the LangChain ChatAnthropic instance."""
    return self.model
```

## 兼容性说明

### 支持的版本

- **LangChain**: >= 1.2.0
- **LangChain Core**: >= 1.2.0
- **LangChain Community**: >= 0.4.0
- **LangGraph**: >= 1.0.0
- **LangChain OpenAI**: >= 1.1.0
- **LangChain Anthropic**: >= 1.3.0

### 破坏性变化

1. **Agent 输入格式**: 必须使用消息列表
2. **Agent 输出格式**: 返回包含消息的状态字典
3. **流式输出**: 事件结构完全不同
4. **工具调用**: 使用 `tool_calls` 属性而不是 `agent_action`

## 验证步骤

### 1. 测试导入

```bash
cd /Users/jory/chatAgent
source venv/bin/activate
python -c "import app; print('✅ App imports successfully!')"
```

### 2. 启动应用

```bash
chainlit run app.py -w
```

### 3. 测试 Agent 模式

1. 打开浏览器访问 `http://localhost:8000`
2. 点击 ⚙️ 设置图标
3. 将"对话模式"切换为 **agent**
4. 提问测试，观察 Agent 思考和工具调用过程

## 迁移检查清单

- [x] 更新 `requirements.txt` 中的包版本
- [x] 运行 `pip install --upgrade -r requirements.txt`
- [x] 更新 `src/agents/react_agent.py` 的导入
- [x] 重构 Agent 创建逻辑使用 LangGraph
- [x] 更新 Agent 调用方式（消息格式）
- [x] 更新流式输出处理
- [x] 更新所有模型 wrapper 的 `get_langchain_llm()` 方法
- [x] 测试应用启动
- [x] 测试 Chat 模式
- [x] 测试 Agent 模式
- [x] 更新文档

## 常见问题

### Q: 为什么要迁移到 LangGraph？

**A**: LangGraph 是 LangChain 团队推出的新架构，专门用于构建复杂的 Agent 和工作流。它提供：
- 更好的状态管理
- 更灵活的控制流
- 更容易调试和可视化
- 更强的类型安全

### Q: 旧的 AgentExecutor 还能用吗？

**A**: 在新版本中，推荐使用 LangGraph 的 `create_react_agent`。虽然 `AgentExecutor` 可能仍然存在，但已不是推荐的方式。

### Q: 升级后遇到其他导入错误怎么办？

**A**: 
1. 检查错误信息中的模块路径
2. 查阅 LangChain 官方文档的迁移指南
3. 使用 `python -c "from module import something"` 测试导入
4. 检查包版本兼容性

## 参考资源

- [LangChain Migration Guide](https://python.langchain.com/docs/versions/migrating)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain API Reference](https://api.python.langchain.com/)
- [Agent Mode Usage Guide](../agent-mode.md)

## 贡献者

如果您在迁移过程中遇到问题或发现改进建议，欢迎：
- 提交 GitHub Issue
- 创建 Pull Request
- 更新本文档

---

**最后更新**: 2024-12-28  
**版本**: 1.0.0  
**状态**: ✅ 已验证

