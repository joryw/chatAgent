# Project Context

## Purpose
[Describe your project's purpose and goals]
这是一个ai agent项目的mvp版本，  想要实现的产品形态想先包含初始的对话能力，随后再来扩展更多的能力

## Tech Stack
- [List your primary technologies]
- [e.g., TypeScript, React, Node.js]
- 目前打算搭建的项目技术栈采用 python语言，langchain来接入模型，对话界面采用Chainlit或Streamlit， 后续如果需要web服务可以考虑采用fastapi

## Project Conventions

### Code Style
[Describe your code style preferences, formatting rules, and naming conventions]
代码要符合python语言规范， 项目结构要清晰， 方法名跟变量名尽可能描述清楚

### Architecture Patterns
[Document your architectural decisions and patterns]
因为项目还没搭建， 这里我的初步设想大概是包含如下的系统架构
应用层(UI)/接口层(API)
业务层(Agent/Chains)
搜索召回层(recall)
模型层(LLMs + Embeddings)
数据层(Data)

### Testing Strategy
[Explain your testing approach and requirements]
可能会先采用从界面的对话能力中验证， 后续看需不需要进行单元测试或模块化测试

### Git Workflow
[Describe your branching strategy and commit conventions]


## Domain Context
[Add domain-specific knowledge that AI assistants need to understand]

## Important Constraints
[List any technical, business, or regulatory constraints]

## External Dependencies
[Document key external services, APIs, or systems]
