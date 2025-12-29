"""ReAct Agent implementation using LangChain."""

import asyncio
import logging
import time
from typing import Optional, AsyncIterator, Any

from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.agents.base import (
    BaseAgent,
    AgentStep,
    AgentResult,
    AgentTimeoutError,
    AgentIterationLimitError,
    AgentExecutionError,
)
from src.agents.tools.search_tool import SearchTool
from src.config.agent_config import AgentConfig
from src.config.langsmith_config import get_langsmith_tracer

logger = logging.getLogger(__name__)


# ReAct Prompt Template (中文版)
REACT_PROMPT_TEMPLATE = """你是一个有用的 AI 助手，可以使用工具来帮助回答用户的问题。

你有权访问以下工具:

{tools}

使用以下格式进行推理和行动:

Question: 用户的输入问题
Thought: 你应该思考如何回答这个问题
Action: 要使用的工具名称，应该是 [{tool_names}] 之一
Action Input: 工具的输入参数
Observation: 工具返回的结果
... (这个 Thought/Action/Action Input/Observation 可以重复 N 次)
Thought: 我现在知道最终答案了
Final Answer: 对用户问题的最终回答

重要规则:
1. 当需要最新信息或实时数据时，使用 web_search 工具
2. 当工具返回结果后，仔细分析是否足够回答问题
3. 如果信息不足，可以再次使用工具搜索更多信息
4. 在最终回答中，使用 [数字] 格式引用搜索结果的来源
5. 最终回答应该准确、完整、有引用

开始!

Question: {input}
Thought: {agent_scratchpad}
"""


class StreamingCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming Agent steps."""
    
    def __init__(self, step_queue: asyncio.Queue):
        """Initialize callback handler.
        
        Args:
            step_queue: Queue to put AgentStep objects
        """
        self.step_queue = step_queue
        self.current_reasoning = ""
    
    async def on_agent_action(
        self, action: AgentAction, **kwargs: Any
    ) -> None:
        """Called when agent takes an action.
        
        Args:
            action: AgentAction object
        """
        # Send reasoning step if we have accumulated text
        if self.current_reasoning:
            await self.step_queue.put(
                AgentStep(
                    type="reasoning",
                    content=self.current_reasoning.strip(),
                )
            )
            self.current_reasoning = ""
        
        # Send action step
        await self.step_queue.put(
            AgentStep(
                type="action",
                content=f"使用工具: {action.tool}",
                metadata={
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                }
            )
        )
    
    async def on_agent_finish(
        self, finish: AgentFinish, **kwargs: Any
    ) -> None:
        """Called when agent finishes.
        
        Args:
            finish: AgentFinish object
        """
        # Send final reasoning if any
        if self.current_reasoning:
            await self.step_queue.put(
                AgentStep(
                    type="reasoning",
                    content=self.current_reasoning.strip(),
                )
            )
        
        # Send final answer
        await self.step_queue.put(
            AgentStep(
                type="final",
                content=finish.return_values.get("output", ""),
            )
        )
    
    async def on_tool_start(
        self, serialized: dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when tool starts.
        
        Args:
            serialized: Tool serialization
            input_str: Tool input string
        """
        tool_name = serialized.get("name", "unknown")
        logger.info(f"🔧 工具开始: {tool_name}, 输入: {input_str}")
    
    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when tool ends.
        
        Args:
            output: Tool output string
        """
        # Send observation step
        await self.step_queue.put(
            AgentStep(
                type="observation",
                content=output,
            )
        )
    
    async def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when tool encounters an error.
        
        Args:
            error: Exception that occurred
        """
        logger.error(f"❌ 工具执行错误: {error}")
        await self.step_queue.put(
            AgentStep(
                type="observation",
                content=f"工具执行失败: {str(error)}",
            )
        )
    
    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token.
        
        Args:
            token: New token string
        """
        # Accumulate reasoning tokens
        self.current_reasoning += token


class ReActAgent(BaseAgent):
    """ReAct Agent implementation.
    
    This agent implements the ReAct (Reasoning + Acting) pattern using LangChain.
    It can use tools (like web search) to gather information before answering.
    
    Supports dual LLM architecture:
    - function_call_llm: Used for tool calling decisions
    - answer_llm: Used for generating final answers
    
    Attributes:
        config: Agent configuration
        function_call_llm: Language model for function calling
        answer_llm: Language model for answer generation
        tools: List of available tools
        agent_executor: LangChain AgentExecutor (uses function_call_llm)
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        search_tool: SearchTool,
        config: Optional[AgentConfig] = None,
        answer_llm: Optional[BaseChatModel] = None,
    ):
        """Initialize ReAct Agent.
        
        Args:
            llm: Language model instance for function calling (function_call_llm)
            search_tool: Search tool instance
            config: Agent configuration (optional)
            answer_llm: Optional language model for answer generation.
                       If None, uses llm for both stages (backward compatibility)
        """
        self.config = config or AgentConfig()
        self.function_call_llm = llm
        # If answer_llm is not provided, use function_call_llm for both stages
        self.answer_llm = answer_llm if answer_llm is not None else llm
        self.tools = [search_tool]
        
        # CRITICAL: Bind tools to the model for function calling
        # LangGraph's create_react_agent requires the model to have tools bound
        # Some models (like DeepSeek) need explicit tool binding
        try:
            # Try to bind tools if the model supports it
            if hasattr(self.function_call_llm, 'bind_tools'):
                logger.info(f"🔧 绑定 {len(self.tools)} 个工具到模型...")
                bound_llm = self.function_call_llm.bind_tools(self.tools)
            else:
                # If bind_tools is not available, use the model as-is
                # LangGraph's create_react_agent should handle tool binding internally
                logger.debug("模型不支持 bind_tools，使用原始模型")
                bound_llm = self.function_call_llm
        except Exception as e:
            logger.warning(f"⚠️ 工具绑定失败，使用原始模型: {e}")
            bound_llm = self.function_call_llm
        
        # Create ReAct agent using LangGraph with function_call_llm
        # LangGraph's create_react_agent handles prompt creation internally
        # It will automatically bind tools if not already bound
        self.agent_executor = create_react_agent(
            model=bound_llm,
            tools=self.tools,
        )
        
        logger.info(f"✅ Agent executor 创建完成，工具数量: {len(self.tools)}")
        
        # Track if using dual LLM mode
        using_dual_llm = answer_llm is not None
        
        # Log tool information for debugging
        tool_names = [tool.name for tool in self.tools]
        logger.info(
            f"✅ ReAct Agent 初始化完成 "
            f"(max_iterations={self.config.max_iterations}, "
            f"max_execution_time={self.config.max_execution_time}s, "
            f"dual_llm_mode={using_dual_llm}, "
            f"tools={tool_names})"
        )
    
    def _should_generate_answer(self, tool_results: list[str], iteration_count: int) -> bool:
        """Evaluate if tool calling results are sufficient to generate answer.
        
        Args:
            tool_results: List of tool execution results
            iteration_count: Number of tool calling iterations performed
            
        Returns:
            True if should generate answer, False if should continue tool calling
        """
        # Stop if reached max iterations
        if iteration_count >= self.config.max_iterations:
            logger.info(f"达到最大迭代次数 ({self.config.max_iterations})，停止工具调用")
            return True
        
        # Stop if we have results and they're not empty
        if tool_results:
            # Check if any result has meaningful content (more than 50 chars)
            meaningful_results = [r for r in tool_results if len(r.strip()) > 50]
            if meaningful_results:
                logger.info(f"工具调用结果充足 ({len(meaningful_results)} 条有效结果)，准备生成回答")
                return True
        
        # Continue tool calling
        return False
    
    async def _generate_answer_with_answer_llm(
        self, 
        user_input: str, 
        tool_results: list[str],
        tool_calls: list[dict]
    ) -> str:
        """Generate final answer using answer_llm based on tool results.
        
        Args:
            user_input: Original user question
            tool_results: List of tool execution results
            tool_calls: List of tool call information
            
        Returns:
            Generated final answer
        """
        # Build context from tool results
        context_parts = []
        for i, result in enumerate(tool_results, 1):
            context_parts.append(f"[搜索结果 {i}]\n{result}")
        
        context = "\n\n".join(context_parts)
        
        # Build prompt for answer generation
        system_prompt = """你是一个有用的 AI 助手。基于以下搜索结果，为用户的问题提供一个准确、完整、有引用的回答。

重要规则:
1. 仔细分析搜索结果，提取相关信息
2. 在回答中使用 [数字] 格式引用搜索结果来源
3. 如果搜索结果不足以回答问题，如实说明
4. 回答应该准确、完整、有条理
"""
        
        user_prompt = f"""用户问题: {user_input}

搜索结果:
{context}

请基于以上搜索结果回答用户的问题。"""
        
        # Generate answer using answer_llm
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        logger.info(f"使用 answer_llm 生成最终回答...")
        response = await self.answer_llm.ainvoke(messages)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return answer
    
    async def run(self, user_input: str) -> AgentResult:
        """Run agent on user input.
        
        Args:
            user_input: User's question
            
        Returns:
            AgentResult with final answer and steps
            
        Raises:
            AgentTimeoutError: If execution exceeds time limit
            AgentExecutionError: If execution fails
        """
        logger.info(f"🤖 Agent 开始执行: {user_input}")
        start_time = time.time()
        
        # Check if using dual LLM mode
        using_dual_llm = self.answer_llm is not self.function_call_llm
        
        try:
            # Get LangSmith tracer if enabled
            tracer = get_langsmith_tracer()
            callbacks = [tracer] if tracer else None
            
            # Run agent with timeout using LangGraph API
            # LangGraph expects messages, not a dict with "input" key
            invoke_input = {"messages": [HumanMessage(content=user_input)]}
            
            # Prepare config with callbacks if LangSmith is enabled
            if callbacks:
                invoke_config = {"callbacks": callbacks}
                result = await asyncio.wait_for(
                    self.agent_executor.ainvoke(invoke_input, config=invoke_config),
                    timeout=self.config.max_execution_time,
                )
            else:
                result = await asyncio.wait_for(
                    self.agent_executor.ainvoke(invoke_input),
                    timeout=self.config.max_execution_time,
                )
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Agent 工具调用阶段完成，耗时 {elapsed_time:.2f}s")
            
            # LangGraph result contains messages
            messages = result.get("messages", [])
            
            # Extract tool results and tool calls
            tool_results = []
            tool_calls = []
            steps = []
            iteration_count = 0
            
            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        iteration_count += 1
                        for tool_call in msg.tool_calls:
                            tool_calls.append({
                                "name": tool_call.get("name"),
                                "args": tool_call.get("args"),
                            })
                            steps.append(
                                AgentStep(
                                    type="action",
                                    content=f"使用工具: {tool_call.get('name', 'unknown')}",
                                    metadata={
                                        "tool": tool_call.get("name"),
                                        "tool_input": tool_call.get("args"),
                                    }
                                )
                            )
                    elif msg.content:
                        # This might be reasoning or final answer from function_call_llm
                        if not using_dual_llm:
                            # Single LLM mode: use this as final answer
                            steps.append(
                                AgentStep(
                                    type="final",
                                    content=msg.content,
                                )
                            )
                elif hasattr(msg, "content") and str(msg.content):
                    # Tool message (observation)
                    tool_results.append(str(msg.content))
                    steps.append(
                        AgentStep(
                            type="observation",
                            content=str(msg.content),
                        )
                    )
            
            # Generate final answer
            if using_dual_llm:
                # Dual LLM mode: use answer_llm to generate final answer
                logger.info("🔄 切换到 answer_llm 生成最终回答...")
                final_answer = await self._generate_answer_with_answer_llm(
                    user_input, tool_results, tool_calls
                )
                steps.append(
                    AgentStep(
                        type="final",
                        content=final_answer,
                    )
                )
            else:
                # Single LLM mode: use the answer from agent_executor
                final_message = messages[-1] if messages else None
                final_answer = final_message.content if final_message else ""
                if not final_answer:
                    # Fallback: generate answer if agent didn't produce one
                    logger.warning("⚠️ Agent 未生成最终回答，使用 answer_llm 生成...")
                    final_answer = await self._generate_answer_with_answer_llm(
                        user_input, tool_results, tool_calls
                    )
                    steps.append(
                        AgentStep(
                            type="final",
                            content=final_answer,
                        )
                    )
            
            total_time = time.time() - start_time
            logger.info(f"✅ Agent 执行完成，总耗时 {total_time:.2f}s")
            
            return AgentResult(
                final_answer=final_answer,
                steps=steps,
                total_iterations=iteration_count,
            )
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            logger.error(f"⏱️ Agent 执行超时 ({elapsed_time:.2f}s)")
            raise AgentTimeoutError(
                f"Agent 执行超时 ({self.config.max_execution_time}秒)。"
                f"请尝试简化问题或切换到 Chat 模式。"
            )
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ Agent 执行失败 ({elapsed_time:.2f}s): {e}")
            raise AgentExecutionError(f"Agent 执行失败: {str(e)}")
    
    async def stream(self, user_input: str) -> AsyncIterator[AgentStep]:
        """Stream agent execution steps.
        
        Args:
            user_input: User's question
            
        Yields:
            AgentStep objects as they are generated
            
        Raises:
            AgentTimeoutError: If execution exceeds time limit
        """
        logger.info(f"🤖 Agent 开始流式执行: {user_input}")
        
        # Check if using dual LLM mode
        using_dual_llm = self.answer_llm is not self.function_call_llm
        
        try:
            # Try streaming first
            has_yielded = False
            all_messages = []
            tool_results = []
            tool_calls = []
            final_answer_from_function_call = None
            
            # Get LangSmith tracer if enabled
            tracer = get_langsmith_tracer()
            callbacks = [tracer] if tracer else None
            
            # Stream events from LangGraph
            stream_input = {"messages": [HumanMessage(content=user_input)]}
            
            # Prepare config with callbacks if LangSmith is enabled
            if callbacks:
                stream_config = {"callbacks": callbacks}
                event_stream = self.agent_executor.astream(stream_input, config=stream_config)
            else:
                event_stream = self.agent_executor.astream(stream_input)
            
            async for event in event_stream:
                has_yielded = True
                # LangGraph returns events with node names as keys
                # e.g., {"agent": {...}, "tools": {...}}
                event_keys = list(event.keys())
                logger.debug(f"收到事件: {event_keys}")
                
                # Log if we're receiving agent events but no tool calls
                if "agent" in event and "tools" not in event_keys:
                    logger.debug(f"🔍 Agent 节点事件，检查是否包含工具调用...")
                
                # Check for agent node (thinking/reasoning)
                if "agent" in event:
                    agent_data = event["agent"]
                    if isinstance(agent_data, dict) and "messages" in agent_data:
                        messages = agent_data["messages"]
                        all_messages.extend(messages)
                        
                        # Check for reasoning (AI message without tool calls)
                        for msg in messages:
                            if isinstance(msg, AIMessage):
                                # Check for tool_calls in multiple possible locations
                                msg_tool_calls = None
                                if hasattr(msg, "tool_calls") and msg.tool_calls:
                                    msg_tool_calls = msg.tool_calls
                                elif hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                                    msg_tool_calls = msg.additional_kwargs.get("tool_calls")
                                
                                if msg_tool_calls:
                                    # This is a tool call decision
                                    logger.info(f"🔧 Agent 决定调用工具，工具调用数量: {len(msg_tool_calls)}")
                                    for tool_call in msg_tool_calls:
                                        # Handle different tool_call formats
                                        if isinstance(tool_call, dict):
                                            tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name", "unknown")
                                            tool_input = tool_call.get("args") or tool_call.get("function", {}).get("arguments", {})
                                        else:
                                            # Handle object format
                                            tool_name = getattr(tool_call, "name", "unknown")
                                            tool_input = getattr(tool_call, "args", {})
                                        
                                        tool_calls.append({
                                            "name": tool_name,
                                            "args": tool_input,
                                        })
                                        logger.info(f"🔧 Agent 决定调用工具: {tool_name}, 输入: {tool_input}")
                                        yield AgentStep(
                                            type="action",
                                            content=f"调用工具: {tool_name}",
                                            metadata={
                                                "tool": tool_name,
                                                "tool_input": str(tool_input),
                                            }
                                        )
                                else:
                                    # This is reasoning or final answer from function_call_llm
                                    content = msg.content
                                    if content and content.strip():
                                        if using_dual_llm:
                                            # In dual LLM mode, this is just reasoning
                                            # We'll generate final answer later
                                            yield AgentStep(
                                                type="reasoning",
                                                content=content[:300] + "..." if len(content) > 300 else content,
                                            )
                                        else:
                                            # In single LLM mode, this might be final answer
                                            if len(all_messages) > 1:
                                                final_answer_from_function_call = content
                                            else:
                                                yield AgentStep(
                                                    type="reasoning",
                                                    content=content[:300] + "..." if len(content) > 300 else content,
                                                )
                
                # Check for tools node (tool execution results)
                elif "tools" in event:
                    tools_data = event["tools"]
                    if isinstance(tools_data, dict) and "messages" in tools_data:
                        tool_messages = tools_data["messages"]
                        all_messages.extend(tool_messages)
                        
                        # Extract tool output
                        for msg in tool_messages:
                            if hasattr(msg, "content"):
                                tool_output = str(msg.content)
                                tool_results.append(tool_output)
                                logger.info(f"✅ 工具执行完成，结果长度: {len(tool_output)}")
                                yield AgentStep(
                                    type="observation",
                                    content=tool_output[:500] + "..." if len(tool_output) > 500 else tool_output,
                                )
            
            # Generate final answer
            if using_dual_llm:
                # Dual LLM mode: use answer_llm to generate final answer
                logger.info("🔄 切换到 answer_llm 生成最终回答...")
                yield AgentStep(
                    type="reasoning",
                    content="正在使用 answer_llm 生成最终回答...",
                )
                
                # Stream answer generation
                system_prompt = """你是一个有用的 AI 助手。基于以下搜索结果，为用户的问题提供一个准确、完整、有引用的回答。

重要规则:
1. 仔细分析搜索结果，提取相关信息
2. 在回答中使用 [数字] 格式引用搜索结果来源
3. 如果搜索结果不足以回答问题，如实说明
4. 回答应该准确、完整、有条理
"""
                
                context_parts = []
                for i, result in enumerate(tool_results, 1):
                    context_parts.append(f"[搜索结果 {i}]\n{result}")
                context = "\n\n".join(context_parts)
                
                user_prompt = f"""用户问题: {user_input}

搜索结果:
{context}

请基于以上搜索结果回答用户的问题。"""
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                # Stream answer generation
                async for chunk in self.answer_llm.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        yield AgentStep(
                            type="final",
                            content=chunk.content,
                        )
            else:
                # Single LLM mode: use answer from function_call_llm
                if not final_answer_from_function_call:
                    # Extract final answer from all messages
                    for msg in reversed(all_messages):
                        if isinstance(msg, AIMessage):
                            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                                final_answer_from_function_call = msg.content
                                break
                
                if final_answer_from_function_call:
                    logger.info("✅ Agent 生成最终答案")
                    yield AgentStep(
                        type="final",
                        content=final_answer_from_function_call,
                    )
                elif not has_yielded:
                    # Fallback: if streaming didn't work, use non-streaming method
                    logger.warning("⚠️ 流式输出未返回事件，使用回退方法")
                    yield AgentStep(
                        type="reasoning",
                        content="正在处理请求...",
                    )
                    result = await self.run(user_input)
                    for step in result.steps:
                        yield step
                else:
                    logger.warning("⚠️ Agent 未生成最终答案")
                    yield AgentStep(
                        type="error",
                        content="Agent 未能生成最终答案，请重试。",
                    )
            
            logger.info("✅ Agent 流式执行完成")
            
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Agent 流式执行超时")
            yield AgentStep(
                type="error",
                content=f"执行超时 ({self.config.max_execution_time}秒)",
            )
        except Exception as e:
            logger.error(f"❌ Agent 流式执行失败: {e}", exc_info=True)
            # Try fallback method
            try:
                logger.info("尝试使用回退方法...")
                yield AgentStep(
                    type="reasoning",
                    content="流式输出遇到问题，使用备用方法处理...",
                )
                result = await self.run(user_input)
                for step in result.steps:
                    yield step
                yield AgentStep(
                    type="final",
                    content=result.final_answer,
                )
            except Exception as fallback_error:
                logger.error(f"回退方法也失败: {fallback_error}")
                yield AgentStep(
                    type="error",
                    content=f"执行失败: {str(e)}",
                )
    
    def reset(self) -> None:
        """Reset agent state."""
        logger.info("🔄 重置 Agent 状态")
        # ReAct agent is stateless, nothing to reset
        pass
    
    def _convert_messages_to_steps(self, messages: list) -> list[AgentStep]:
        """Convert LangGraph messages to AgentStep objects.
        
        Args:
            messages: List of messages from LangGraph
            
        Returns:
            List of AgentStep objects
        """
        steps = []
        
        for msg in messages:
            # Skip human messages (user input)
            if isinstance(msg, HumanMessage):
                continue
            
            # AI messages are responses
            if isinstance(msg, AIMessage):
                if msg.tool_calls:
                    # This is a tool call
                    for tool_call in msg.tool_calls:
                        steps.append(
                            AgentStep(
                                type="action",
                                content=f"使用工具: {tool_call.get('name', 'unknown')}",
                                metadata={
                                    "tool": tool_call.get("name"),
                                    "tool_input": tool_call.get("args"),
                                }
                            )
                        )
                else:
                    # Final answer
                    steps.append(
                        AgentStep(
                            type="final",
                            content=msg.content,
                        )
                    )
            
            # Tool messages are observations
            else:
                steps.append(
                    AgentStep(
                        type="observation",
                        content=str(msg.content),
                    )
                )
        
        return steps

