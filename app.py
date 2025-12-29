"""Main Chainlit application for AI Agent with Model Invocation."""

import asyncio
import logging
import os
from typing import Optional

import chainlit as cl
from chainlit.input_widget import Switch, Select
from dotenv import load_dotenv

from src.config.model_config import (
    ModelProvider,
    get_model_config,
    get_available_providers,
)
from src.config.search_config import get_search_config, is_search_available
from src.config.agent_config import (
    get_agent_config, 
    get_default_mode,
    create_agent_llms_from_config,
)
from src.config.langsmith_config import is_langsmith_enabled, get_langsmith_config
from src.models.factory import get_model_wrapper
from src.prompts.templates import (
    DEFAULT_SYSTEM_MESSAGE,
    count_prompt_tokens,
    build_system_message_with_search,
)
from src.search.search_service import SearchService
from src.search.citation_processor import CitationProcessor
from src.agents import ReActAgent, AgentStep
from src.agents.tools import create_search_tool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global caches (initialized once at first session start)
_global_search_service: Optional[SearchService] = None
_search_service_initialized = False
_search_initialization_lock = asyncio.Lock()

_global_model_wrappers = {}  # Cache for model wrappers by provider
_model_initialization_lock = asyncio.Lock()


async def get_or_create_model_wrapper(provider: str):
    """Get cached model wrapper or create new one.
    
    Model wrappers are cached per provider to avoid repeated initialization.
    """
    global _global_model_wrappers
    
    # Return cached wrapper if exists
    if provider in _global_model_wrappers:
        logger.debug(f"Reusing cached model wrapper for provider: {provider}")
        return _global_model_wrappers[provider]
    
    async with _model_initialization_lock:
        # Double-check after acquiring lock
        if provider in _global_model_wrappers:
            return _global_model_wrappers[provider]
        
        # Create new wrapper
        logger.info(f"🤖 Initializing model wrapper for provider: {provider} (one-time setup)...")
        model_wrapper = get_model_wrapper(provider=provider)
        _global_model_wrappers[provider] = model_wrapper
        logger.info(f"✅ Model wrapper initialized: {model_wrapper.config.model_name}")
        
        return model_wrapper


async def initialize_search_service() -> Optional[SearchService]:
    """Initialize search service once and cache the result.
    
    This function is called only once when the first user session starts.
    Subsequent sessions will reuse the cached search service.
    """
    global _global_search_service, _search_service_initialized
    
    # Double-check pattern with lock
    if _search_service_initialized:
        return _global_search_service
    
    async with _search_initialization_lock:
        # Check again after acquiring lock
        if _search_service_initialized:
            return _global_search_service
        
        search_available = is_search_available()
        if not search_available:
            _search_service_initialized = True
            return None
        
        try:
            logger.info("🔍 Initializing search service (one-time setup)...")
            search_config = get_search_config()
            search_service = SearchService(
                searxng_url=search_config.searxng_url,
                timeout=search_config.timeout,
                max_results=search_config.max_results,
                max_content_length=search_config.max_content_length,
            )
            
            # Perform one-time health check
            health_ok = await search_service.client.health_check()
            
            if health_ok:
                logger.info("✅ Search service initialized successfully")
                _global_search_service = search_service
            else:
                logger.warning(
                    "⚠️ SearXNG health check failed. Search will be unavailable.\n"
                    "📖 Deployment guide: docs/guides/searxng-deployment.md"
                )
                _global_search_service = None
        
        except Exception as e:
            logger.error(
                f"❌ Failed to initialize search service: {str(e)}\n"
                "Search functionality will be unavailable.\n"
                "To enable search:\n"
                "  1. Deploy SearXNG locally (see docs/guides/searxng-deployment.md)\n"
                "  2. Ensure SEARXNG_URL in .env points to your instance\n"
                "  3. Run verification: bash openspec/changes/update-searxng-local-deployment/verify-searxng.sh"
            )
            _global_search_service = None
        
        _search_service_initialized = True
        return _global_search_service


@cl.on_settings_update
async def settings_update(settings):
    """Handle chat settings updates."""
    try:
        # Handle conversation mode switch
        conversation_mode = settings.get("conversation_mode")
        current_mode = cl.user_session.get("conversation_mode", "chat")
        
        if conversation_mode and conversation_mode != current_mode:
            # Mode switched - reset conversation
            cl.user_session.set("conversation_mode", conversation_mode)
            cl.user_session.set("conversation_history", [])
            
            # Re-initialize agent if switching to agent mode
            if conversation_mode == "agent":
                model_wrapper = cl.user_session.get("model_wrapper")
                search_service = cl.user_session.get("search_service")
                
                if model_wrapper and search_service:
                    # Create agent
                    search_tool = create_search_tool(search_service)
                    agent_config = get_agent_config()
                    
                    # Create LLMs from config (supports dual LLM mode)
                    current_provider = cl.user_session.get("current_provider", "openai")
                    function_call_llm, answer_llm = create_agent_llms_from_config(
                        default_provider=current_provider,
                        agent_config=agent_config
                    )
                    
                    agent = ReActAgent(
                        llm=function_call_llm,
                        search_tool=search_tool,
                        config=agent_config,
                        answer_llm=answer_llm,
                    )
                    cl.user_session.set("agent", agent)
                    
                    mode_display = "🤖 Agent 模式"
                    mode_desc = "模型会自主决策何时使用搜索工具"
                else:
                    mode_display = "🤖 Agent 模式（搜索不可用）"
                    mode_desc = "搜索服务未启用，Agent 功能受限"
            else:
                mode_display = "💬 Chat 模式"
                mode_desc = "常规对话，可手动控制搜索"
            
            await cl.Message(
                content=f"✅ 已切换到 {mode_display}\n\n{mode_desc}\n\n对话历史已清除。",
                author="System",
            ).send()
        
        # Handle web search toggle (only in Chat mode)
        search_enabled = settings.get("web_search", False)
        search_service = cl.user_session.get("search_service")
        current_mode = cl.user_session.get("conversation_mode", "chat")
        
        if current_mode == "chat" and search_service:
            # Update search enabled state
            cl.user_session.set("search_enabled", search_enabled)
            
            # Send confirmation message
            status = "✅ 已启用" if search_enabled else "❌ 已禁用"
            await cl.Message(
                content=f"联网搜索 {status}",
                author="System",
            ).send()
        elif current_mode == "agent" and "web_search" in settings:
            # In Agent mode, search is always controlled by the agent
            await cl.Message(
                content="ℹ️ Agent 模式下，搜索由模型自主决策，无需手动控制。",
                author="System",
            ).send()
        
        # Handle DeepSeek model variant selection
        deepseek_model = settings.get("deepseek_model")
        current_provider = cl.user_session.get("current_provider")
        
        if deepseek_model and current_provider == "deepseek":
            # Update model variant
            model_wrapper = cl.user_session.get("model_wrapper")
            if model_wrapper:
                # Update model name and variant
                model_wrapper.config.model_name = deepseek_model
                model_wrapper.config.model_variant = deepseek_model
                
                # Update max_tokens based on model variant
                # deepseek-chat: max 8K, deepseek-reasoner: max 64K
                if deepseek_model == "deepseek-reasoner":
                    # Ensure max_tokens is within reasoner's limit (64K)
                    if model_wrapper.config.max_tokens > 65536:
                        model_wrapper.config.max_tokens = 65536
                else:
                    # Ensure max_tokens is within chat's limit (8K)
                    if model_wrapper.config.max_tokens > 8192:
                        model_wrapper.config.max_tokens = 8192
                
                # Clear conversation history
                cl.user_session.set("conversation_history", [])
                
                # Send confirmation message
                model_display = "💭 推理模型" if deepseek_model == "deepseek-reasoner" else "💬 对话模型"
                max_output = "64K" if deepseek_model == "deepseek-reasoner" else "8K"
                await cl.Message(
                    content=f"✅ 已切换到 DeepSeek {model_display}\n\n模型: {deepseek_model}\n最大输出: {max_output}\n对话历史已清除。",
                    author="System",
                ).send()
    
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        await cl.Message(
            content=f"❌ 设置更新失败: {str(e)}",
            author="System",
        ).send()


@cl.on_chat_start
async def start():
    """Initialize chat session."""
    try:
        # Initialize LangSmith monitoring (if configured)
        langsmith_enabled = is_langsmith_enabled()
        if langsmith_enabled:
            langsmith_config = get_langsmith_config()
            logger.info(
                f"📊 LangSmith 监控已启用 (项目: {langsmith_config.project})"
            )
        else:
            logger.debug("LangSmith 监控未启用（未配置 API 密钥）")
        
        # Get available providers
        available_providers = get_available_providers()
        
        if not available_providers:
            await cl.Message(
                content="⚠️ No model providers configured. Please set up API keys in .env file.",
                author="System",
            ).send()
            return
        
        # Get default provider
        default_provider = os.getenv("DEFAULT_PROVIDER", "openai")
        if default_provider not in available_providers:
            default_provider = available_providers[0]
        
        # Get cached model wrapper (initialized once per provider)
        try:
            model_wrapper = await get_or_create_model_wrapper(provider=default_provider)
            config = model_wrapper.config
            
            # Get cached search service (initialized once on first session)
            search_service = await initialize_search_service()
            search_available = search_service is not None
            
            # Get default conversation mode
            default_mode = get_default_mode()
            
            # Initialize agent if in agent mode and search is available
            agent = None
            if default_mode == "agent" and search_service:
                try:
                    logger.info("🤖 Initializing Agent mode...")
                    search_tool = create_search_tool(search_service)
                    agent_config = get_agent_config()
                    
                    # Create LLMs from config (supports dual LLM mode)
                    function_call_llm, answer_llm = create_agent_llms_from_config(
                        default_provider=default_provider,
                        agent_config=agent_config
                    )
                    
                    agent = ReActAgent(
                        llm=function_call_llm,
                        search_tool=search_tool,
                        config=agent_config,
                        answer_llm=answer_llm,
                    )
                    logger.info("✅ Agent initialized successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Agent: {e}")
                    default_mode = "chat"  # Fallback to chat mode
            
            # Store in session
            cl.user_session.set("model_wrapper", model_wrapper)
            cl.user_session.set("current_provider", default_provider)
            cl.user_session.set("available_providers", available_providers)
            cl.user_session.set("conversation_history", [])
            cl.user_session.set("search_service", search_service)
            # Get default search enabled state from config (Chat mode only, Agent mode controls search automatically)
            search_config = get_search_config()
            default_search_enabled = search_config.enabled if default_mode == "chat" else False
            cl.user_session.set("search_enabled", default_search_enabled)
            cl.user_session.set("conversation_mode", default_mode)
            cl.user_session.set("agent", agent)
            
            # Prepare welcome message first
            if search_available and search_service:
                search_status = "✅ 可用 (本地部署)"
                search_hint = ""
            else:
                search_status = "❌ 不可用"
                search_hint = "\n\n💡 **启用联网搜索:**\n1. 部署 SearXNG: `docs/guides/searxng-deployment.md`\n2. 配置 `.env`: `SEARXNG_URL=http://localhost:8080`\n3. 重启应用\n"
            
            # Build model info
            model_info = f"**Current Model:** {config.model_name}"
            if default_provider == "deepseek" and config.model_variant:
                model_type = "💭 推理模型" if config.model_variant == "deepseek-reasoner" else "💬 对话模型"
                model_info += f" ({model_type})"
            
            # Build conversation mode info
            mode_emoji = "🤖" if default_mode == "agent" else "💬"
            mode_name = "Agent 模式" if default_mode == "agent" else "Chat 模式"
            if default_mode == "agent":
                if search_available:
                    mode_desc = "模型会自主决策何时使用搜索工具"
                else:
                    mode_desc = "搜索服务未启用，Agent 功能受限"
            else:
                mode_desc = "常规对话，可手动控制搜索"
            
            # Build UI settings hint
            ui_settings_hint = f"""**💡 使用 UI 设置面板:**
- 点击右上角 ⚙️ 图标打开设置面板
- 选择 \"🔀 对话模式\" 切换 Chat/Agent 模式
- 在 Chat 模式下可切换 "🔍 联网搜索" 开关"""
            
            if default_provider == "deepseek":
                ui_settings_hint += "\n- 选择 \"🤖 DeepSeek 模型\" 可切换对话/推理模型"
            
            ui_settings_hint += "\n- 设置会立即生效"
            
            welcome_msg = f"""# 🤖 Welcome to AI Agent Chat!

{model_info}
**Provider:** {config.provider}
**Temperature:** {config.temperature}
**Max Tokens:** {config.max_tokens}

**Available Providers:** {', '.join(available_providers)}
**联网搜索:** {search_status}{search_hint}

**对话模式:** {mode_emoji} {mode_name} - {mode_desc}

You can start chatting now! Type your message below.

{ui_settings_hint}

**Commands (备用方式):**
- `/switch <provider>` - Switch to a different model provider
- `/mode <chat|agent>` - Switch conversation mode
- `/search <on|off>` - Enable or disable web search (Chat mode only)
- `/config` - View current configuration
- `/reset` - Clear conversation history
- `/help` - Show this help message
"""
            
            # Send welcome message and chat settings simultaneously
            # This prevents showing a blank screen before content appears
            welcome_message = cl.Message(
                content=welcome_msg,
                author="System",
            )
            
            # Build settings widgets
            settings_widgets = [
                Select(
                    id="conversation_mode",
                    label="🔀 对话模式",
                    values=["chat", "agent"],
                    initial_value=default_mode,
                    description="Chat: 常规对话 | Agent: 自主决策搜索",
                ),
                Switch(
                    id="web_search",
                    label="🔍 联网搜索 (Chat模式)",
                    initial=default_search_enabled,
                    description="仅在 Chat 模式下有效，Agent 模式由模型自主决策",
                    disabled=(search_service is None),
                )
            ]
            
            # Add DeepSeek model selection if using DeepSeek provider
            if default_provider == "deepseek":
                current_variant = config.model_variant or "deepseek-chat"
                settings_widgets.append(
                    Select(
                        id="deepseek_model",
                        label="🤖 DeepSeek 模型",
                        values=["deepseek-chat", "deepseek-reasoner"],
                        initial_value=current_variant,
                        description="选择 DeepSeek 模型类型",
                    )
                )
            
            chat_settings = cl.ChatSettings(settings_widgets)
            
            # Send both at the same time to avoid double window flash
            await asyncio.gather(
                welcome_message.send(),
                chat_settings.send()
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            await cl.Message(
                content=f"❌ Error initializing model: {str(e)}\n\nPlease check your .env configuration.",
                author="System",
            ).send()
    
    except Exception as e:
        logger.error(f"Error in chat start: {str(e)}")
        await cl.Message(
            content=f"❌ Initialization error: {str(e)}",
            author="System",
        ).send()




@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    try:
        user_message = message.content.strip()
        
        # Handle commands
        if user_message.startswith("/"):
            await handle_command(user_message)
            return
        
        # Get model wrapper from session
        model_wrapper = cl.user_session.get("model_wrapper")
        if not model_wrapper:
            await cl.Message(
                content="⚠️ Model not initialized. Please restart the chat.",
                author="System",
            ).send()
            return
        
        # Check conversation mode
        conversation_mode = cl.user_session.get("conversation_mode", "chat")
        
        # Route to appropriate handler
        if conversation_mode == "agent":
            await handle_agent_mode(user_message)
        else:
            await handle_chat_mode(user_message)
    
    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")
        await cl.Message(
            content=f"❌ Error: {str(e)}",
            author="System",
        ).send()


async def handle_agent_mode(user_message: str):
    """Handle Agent mode conversation.
    
    Args:
        user_message: User's input message
    """
    try:
        agent = cl.user_session.get("agent")
        if not agent:
            await cl.Message(
                content="⚠️ Agent 未初始化。请切换到 Chat 模式或重启会话。",
                author="System",
            ).send()
            return
        
        logger.info(f"🤖 Agent 模式处理: {user_message}")
        
        # Track steps for better UI handling
        thinking_step = None
        current_action_step = None
        
        # Stream agent execution with timeout
        try:
            async for step in agent.stream(user_message):
                logger.debug(f"收到 Agent 步骤: type={step.type}, content_length={len(step.content) if step.content else 0}")
                
                if step.type == "reasoning":
                    # Show thinking process in collapsible step
                    if thinking_step is None:
                        thinking_step = cl.Step(name="💭 思考中", type="tool")
                        await thinking_step.__aenter__()
                    thinking_step.output = step.content
                
                elif step.type == "action":
                    # Close thinking step if open
                    if thinking_step:
                        await thinking_step.__aexit__(None, None, None)
                        thinking_step = None
                    
                    # Show tool call
                    tool_name = step.metadata.get("tool", "unknown") if step.metadata else "unknown"
                    tool_input = step.metadata.get("tool_input", "") if step.metadata else ""
                    current_action_step = cl.Step(name=f"🛠️ 使用工具: {tool_name}", type="tool")
                    await current_action_step.__aenter__()
                    current_action_step.output = f"输入参数: {tool_input}"
                
                elif step.type == "observation":
                    # Close action step if open
                    if current_action_step:
                        await current_action_step.__aexit__(None, None, None)
                        current_action_step = None
                    
                    # Show tool result
                    async with cl.Step(name="💡 工具结果", type="tool") as observation_step:
                        observation_step.output = step.content
                
                elif step.type == "final":
                    # Close any open steps
                    if thinking_step:
                        await thinking_step.__aexit__(None, None, None)
                        thinking_step = None
                    if current_action_step:
                        await current_action_step.__aexit__(None, None, None)
                        current_action_step = None
                    
                    # Show final answer
                    final_msg = cl.Message(
                        content=step.content,
                        author="Assistant",
                    )
                    await final_msg.send()
                    
                    # Update conversation history
                    history = cl.user_session.get("conversation_history", [])
                    history.append({
                        "role": "user",
                        "content": user_message,
                    })
                    history.append({
                        "role": "assistant",
                        "content": step.content,
                    })
                    cl.user_session.set("conversation_history", history)
                    break  # Exit loop after final answer
                
                elif step.type == "error":
                    # Close any open steps
                    if thinking_step:
                        await thinking_step.__aexit__(None, None, None)
                        thinking_step = None
                    if current_action_step:
                        await current_action_step.__aexit__(None, None, None)
                        current_action_step = None
                    
                    # Show error
                    await cl.Message(
                        content=f"❌ Agent 执行错误: {step.content}",
                        author="System",
                    ).send()
                    break  # Exit loop on error
            
            # Ensure all steps are closed
            if thinking_step:
                try:
                    await thinking_step.__aexit__(None, None, None)
                except:
                    pass
            if current_action_step:
                try:
                    await current_action_step.__aexit__(None, None, None)
                except:
                    pass
            
            logger.info("✅ Agent 模式处理完成")
        
        except asyncio.TimeoutError:
            logger.error("⏱️ Agent 执行超时")
            await cl.Message(
                content="⏱️ Agent 执行超时，请尝试简化问题或切换到 Chat 模式。",
                author="System",
            ).send()
        except Exception as stream_error:
            logger.error(f"❌ Agent 流式处理错误: {stream_error}", exc_info=True)
            await cl.Message(
                content=f"❌ Agent 执行失败: {str(stream_error)}\n\n请尝试切换到 Chat 模式。",
                author="System",
            ).send()
    
    except Exception as e:
        logger.error(f"❌ Agent 模式错误: {str(e)}", exc_info=True)
        await cl.Message(
            content=f"❌ Agent 执行失败: {str(e)}\n\n请尝试切换到 Chat 模式。",
            author="System",
        ).send()


async def handle_chat_mode(user_message: str):
    """Handle Chat mode conversation.
    
    Args:
        user_message: User's input message
    """
    try:
        # Get model wrapper from session
        model_wrapper = cl.user_session.get("model_wrapper")
        if not model_wrapper:
            await cl.Message(
                content="⚠️ Model not initialized. Please restart the chat.",
                author="System",
            ).send()
            return
        
        # Check if search is enabled
        search_enabled = cl.user_session.get("search_enabled", False)
        search_service = cl.user_session.get("search_service")
        
        # Perform search if enabled
        search_response = None
        search_results_text = None
        if search_enabled and search_service:
            try:
                # Show searching indicator
                search_msg = cl.Message(
                    content="🔍 正在搜索相关信息...",
                    author="System",
                )
                await search_msg.send()
                
                # Perform search
                search_response = await search_service.search(user_message)
                
                # Update search message
                if search_response and not search_response.is_empty():
                    search_msg.content = f"✅ 找到 {search_response.total_results} 条搜索结果"
                    await search_msg.update()
                    
                    # Format search results for prompt
                    search_results_text = search_service.format_for_prompt(search_response)
                else:
                    search_msg.content = "⚠️ 未找到相关搜索结果，将基于模型知识回答"
                    await search_msg.update()
            
            except Exception as e:
                logger.error(f"Search error: {str(e)}")
                await cl.Message(
                    content=f"⚠️ 搜索失败: {str(e)}\n\n将继续使用模型知识回答。",
                    author="System",
                ).send()
        
        try:
            # Build system message with search results if available
            system_message = build_system_message_with_search(
                DEFAULT_SYSTEM_MESSAGE,
                search_results_text,
            )
            
            # Count tokens
            token_count = count_prompt_tokens(
                user_message,
                system_message,
            )
            
            logger.info(f"Processing message with {token_count} tokens (search: {search_enabled})")
            
            # Check if using deepseek-reasoner
            config = model_wrapper.config
            is_reasoner = (
                config.provider == "deepseek" and 
                config.model_variant == "deepseek-reasoner"
            )
            
            # Generate streaming response
            thinking_step = None
            reasoning_content = ""
            full_response = ""
            response_msg = None
            
            try:
                async for chunk in model_wrapper.generate_stream(
                    prompt=user_message,
                    system_message=system_message,
                ):
                    # Skip if chunk is None or missing required attributes
                    if chunk is None:
                        logger.warning("Received None chunk from model")
                        continue
                    if not hasattr(chunk, 'content') or chunk.content is None:
                        logger.warning(f"Chunk missing content: {chunk}")
                        continue
                    if not hasattr(chunk, 'chunk_type'):
                        logger.warning(f"Chunk missing chunk_type: {chunk}")
                        continue
                    
                    # Handle reasoning content (only for deepseek-reasoner)
                    if chunk.chunk_type == "reasoning":
                        if thinking_step is None:
                            # Create thinking message for real-time expanded view
                            logger.info("💭 Creating thinking message (expanded for streaming)")
                            thinking_step = cl.Message(
                                content="",
                                author="💭 思考中",
                            )
                            await thinking_step.send()
                            logger.debug("Thinking message created for real-time streaming")
                        
                        # Stream reasoning content in real-time
                        reasoning_content += chunk.content
                        thinking_step.content = reasoning_content
                        await thinking_step.update()
                    
                    # Handle answer content
                    elif chunk.chunk_type == "answer":
                        # Convert thinking message to collapsible step on first answer chunk
                        if thinking_step is not None:
                            if not hasattr(thinking_step, '_collapsed_already'):
                                logger.info("💡 Converting thinking to collapsed step (answer started)")
                                
                                # Create a collapsed Step with the thinking content
                                collapsed_step = cl.Step(name="💡 思考过程", type="tool")
                                collapsed_step.output = reasoning_content
                                
                                # Use context manager to create collapsed step
                                async with collapsed_step:
                                    pass  # Step automatically closes after context
                                
                                # Remove the expanded thinking message
                                thinking_step.content = ""
                                await thinking_step.remove()
                                
                                # Mark as collapsed to ensure idempotency
                                thinking_step._collapsed_already = True
                                logger.debug("Thinking converted to collapsed step successfully")
                        
                        # Create response message if not exists
                        if response_msg is None:
                            response_msg = cl.Message(
                                content="",
                                author="Assistant",
                            )
                            await response_msg.send()
                        
                        # Stream answer content in real-time
                        full_response += chunk.content
                        response_msg.content = full_response
                        await response_msg.update()
            
            finally:
                # Ensure thinking message is converted to collapsed step even in case of errors
                if thinking_step is not None and not hasattr(thinking_step, '_collapsed_already'):
                    logger.info("💡 Converting thinking to collapsed step (cleanup)")
                    try:
                        # Create a collapsed Step with the thinking content
                        collapsed_step = cl.Step(name="💡 思考过程", type="tool")
                        collapsed_step.output = reasoning_content
                        
                        # Use context manager to create collapsed step
                        async with collapsed_step:
                            pass  # Step automatically closes after context
                        
                        # Remove the expanded thinking message
                        if hasattr(thinking_step, 'remove'):
                            thinking_step.content = ""
                            await thinking_step.remove()
                        
                        logger.debug("Thinking cleanup completed")
                    except Exception as cleanup_error:
                        logger.error(f"Error during thinking step cleanup: {cleanup_error}")
            
            # Process inline citations if search was used
            if search_response and not search_response.is_empty() and response_msg:
                try:
                    logger.info("🔗 Processing inline citations")
                    citation_processor = CitationProcessor(search_response)
                    processed_response = citation_processor.process_response(full_response)
                    
                    # Update the response message with clickable citations
                    response_msg.content = processed_response
                    await response_msg.update()
                    
                    logger.info("✅ Inline citations processed successfully")
                except Exception as e:
                    logger.error(f"Failed to process citations: {e}")
                    # Continue without citations on error
            
            # Display search sources if available
            if search_response and not search_response.is_empty():
                sources_text = search_service.format_sources(search_response)
                await cl.Message(
                    content=sources_text,
                    author="System",
                ).send()
            
            # Update conversation history
            history = cl.user_session.get("conversation_history", [])
            history.append({
                "role": "user",
                "content": user_message,
            })
            history.append({
                "role": "assistant",
                "content": full_response,
            })
            cl.user_session.set("conversation_history", history)
            
            # Count completion tokens (approximate)
            completion_tokens = model_wrapper.count_tokens(full_response)
            total_tokens = token_count + completion_tokens
            
            # Send metadata as a separate message
            search_info = f"\n- Search: {'Enabled ✅' if search_enabled else 'Disabled'}"
            if search_enabled and search_response:
                search_info += f" ({search_response.total_results} results)"
            
            metadata_msg = f"""
---
**📊 Response Metadata:**
- Model: {model_wrapper.config.model_name}
- Tokens Used: ~{total_tokens} (prompt: ~{token_count}, completion: ~{completion_tokens}){search_info}
"""
            
            await cl.Message(
                content=metadata_msg,
                author="System",
            ).send()
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            if response_msg is not None:
                response_msg.content = f"❌ Error generating response: {str(e)}\n\nPlease try again."
                await response_msg.update()
            else:
                await cl.Message(
                    content=f"❌ Error generating response: {str(e)}\n\nPlease try again.",
                    author="Assistant",
                ).send()
    
    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")
        await cl.Message(
            content=f"❌ Error: {str(e)}",
            author="System",
        ).send()


async def handle_command(command: str):
    """Handle slash commands.
    
    Args:
        command: Command string (e.g., '/switch openai')
    """
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    if cmd == "/help":
        current_provider = cl.user_session.get("current_provider", "")
        
        # Build UI settings hint
        ui_hint = """**💡 推荐使用 UI 设置面板:**
- 点击右上角 ⚙️ 图标打开设置面板
- 直接切换 "🔍 联网搜索" 开关"""
        
        if current_provider == "deepseek":
            ui_hint += "\n- 选择 \"🤖 DeepSeek 模型\" 可切换对话/推理模型"
        
        help_msg = f"""# 📖 Available Commands

{ui_hint}

**命令列表 (备用方式):**
- `/switch <provider>` - Switch to a different model provider (openai, anthropic, deepseek)
- `/mode <chat|agent>` - Switch conversation mode (推荐使用UI切换)
- `/search <on|off>` - Enable or disable web search (仅Chat模式，推荐使用UI开关)
- `/config` - View current configuration
- `/reset` - Clear conversation history
- `/help` - Show this help message

**Examples:**
```
/switch deepseek
/mode agent
/mode chat
/search on
/search off
```

**🔀 对话模式:**
- **Chat 模式** (💬): 常规对话，可手动控制联网搜索
- **Agent 模式** (🤖): 模型自主决策何时使用搜索工具，实现 ReAct 循环

**💭 DeepSeek Reasoner 模型:**
- 选择 deepseek-reasoner 后，模型会先展示思考过程
- 思考内容会在开始回答时自动折叠
- 可点击 "💡 思考过程" 展开查看
"""
        await cl.Message(content=help_msg, author="System").send()
    
    elif cmd == "/config":
        model_wrapper = cl.user_session.get("model_wrapper")
        if not model_wrapper:
            await cl.Message(
                content="⚠️ No model configured.",
                author="System",
            ).send()
            return
        
        config = model_wrapper.config
        search_enabled = cl.user_session.get("search_enabled", False)
        search_service = cl.user_session.get("search_service")
        conversation_mode = cl.user_session.get("conversation_mode", "chat")
        
        search_status = "✅ Enabled" if search_enabled else "❌ Disabled"
        if not search_service:
            search_status = "⚠️ Not Available"
        
        mode_emoji = "🤖" if conversation_mode == "agent" else "💬"
        mode_name = "Agent 模式" if conversation_mode == "agent" else "Chat 模式"
        
        # Build model info
        model_info = f"**Model:** {config.model_name}"
        if config.provider == "deepseek" and config.model_variant:
            model_type = "💭 推理模型" if config.model_variant == "deepseek-reasoner" else "💬 对话模型"
            model_info += f"\n**Model Type:** {model_type}"
        
        # Build UI hints
        ui_hints = "💡 **提示:** 可通过右上角 ⚙️ 设置面板切换对话模式和联网搜索"
        if config.provider == "deepseek":
            ui_hints += "\n💡 **DeepSeek 用户:** 可在设置面板中切换对话/推理模型"
        
        config_msg = f"""# ⚙️ Current Configuration

**Provider:** {config.provider}
{model_info}
**Temperature:** {config.temperature}
**Max Tokens:** {config.max_tokens}
**Top P:** {config.top_p}
**Timeout:** {config.timeout}s

**Conversation Mode:** {mode_emoji} {mode_name}
**Web Search:** {search_status}

**Available Providers:** {', '.join(cl.user_session.get('available_providers', []))}

{ui_hints}
"""
        await cl.Message(content=config_msg, author="System").send()
    
    elif cmd == "/reset":
        cl.user_session.set("conversation_history", [])
        await cl.Message(
            content="✅ Conversation history cleared.",
            author="System",
        ).send()
    
    elif cmd == "/mode":
        if not args:
            current_mode = cl.user_session.get("conversation_mode", "chat")
            mode_display = "🤖 Agent 模式" if current_mode == "agent" else "💬 Chat 模式"
            await cl.Message(
                content=f"""# 🔀 Current Conversation Mode

**Current Mode:** {mode_display}

**Available Modes:**
- `chat` - 💬 常规对话，可手动控制搜索
- `agent` - 🤖 自主决策搜索工具使用

To change: `/mode chat` or `/mode agent`
""",
                author="System",
            ).send()
            return
        
        mode = args.lower().strip()
        if mode not in ["chat", "agent"]:
            await cl.Message(
                content="⚠️ Invalid mode. Use `/mode chat` or `/mode agent`",
                author="System",
            ).send()
            return
        
        current_mode = cl.user_session.get("conversation_mode", "chat")
        if mode == current_mode:
            await cl.Message(
                content=f"ℹ️ Already in {mode} mode.",
                author="System",
            ).send()
            return
        
        # Switch mode
        cl.user_session.set("conversation_mode", mode)
        cl.user_session.set("conversation_history", [])
        
        # Initialize agent if switching to agent mode
        if mode == "agent":
            model_wrapper = cl.user_session.get("model_wrapper")
            search_service = cl.user_session.get("search_service")
            
            if model_wrapper and search_service:
                try:
                    search_tool = create_search_tool(search_service)
                    agent_config = get_agent_config()
                    
                    # Create LLMs from config (supports dual LLM mode)
                    current_provider = cl.user_session.get("current_provider", "openai")
                    function_call_llm, answer_llm = create_agent_llms_from_config(
                        default_provider=current_provider,
                        agent_config=agent_config
                    )
                    
                    agent = ReActAgent(
                        llm=function_call_llm,
                        search_tool=search_tool,
                        config=agent_config,
                        answer_llm=answer_llm,
                    )
                    cl.user_session.set("agent", agent)
                    
                    await cl.Message(
                        content="✅ 已切换到 🤖 **Agent 模式**\n\n模型会自主决策何时使用搜索工具。\n对话历史已清除。",
                        author="System",
                    ).send()
                except Exception as e:
                    logger.error(f"Failed to initialize agent: {e}")
                    await cl.Message(
                        content=f"❌ Agent 初始化失败: {str(e)}\n\n已回退到 Chat 模式。",
                        author="System",
                    ).send()
                    cl.user_session.set("conversation_mode", "chat")
            else:
                await cl.Message(
                    content="⚠️ 搜索服务不可用，无法启用 Agent 模式。\n\n请先配置 SearXNG。",
                    author="System",
                ).send()
                cl.user_session.set("conversation_mode", "chat")
        else:
            await cl.Message(
                content="✅ 已切换到 💬 **Chat 模式**\n\n可手动控制联网搜索。\n对话历史已清除。",
                author="System",
            ).send()
    
    elif cmd == "/search":
        if not args:
            search_enabled = cl.user_session.get("search_enabled", False)
            search_service = cl.user_session.get("search_service")
            
            if not search_service:
                await cl.Message(
                    content="⚠️ Web search is not available. Please check your SEARXNG_URL configuration.",
                    author="System",
                ).send()
                return
            
            status = "✅ Enabled" if search_enabled else "❌ Disabled"
            await cl.Message(
                content=f"""# 🔍 Web Search Status

**Current Status:** {status}

To change: `/search on` or `/search off`
""",
                author="System",
            ).send()
            return
        
        action = args.lower().strip()
        search_service = cl.user_session.get("search_service")
        
        if not search_service:
            await cl.Message(
                content="⚠️ Web search is not available. Please check your SEARXNG_URL configuration.",
                author="System",
            ).send()
            return
        
        if action == "on":
            cl.user_session.set("search_enabled", True)
            await cl.Message(
                content="✅ Web search **enabled**\n\nNow you can ask questions that require real-time information!",
                author="System",
            ).send()
        elif action == "off":
            cl.user_session.set("search_enabled", False)
            await cl.Message(
                content="❌ Web search **disabled**\n\nThe AI will respond using its built-in knowledge only.",
                author="System",
            ).send()
        else:
            await cl.Message(
                content="⚠️ Invalid option. Use `/search on` or `/search off`",
                author="System",
            ).send()
    
    elif cmd == "/switch":
        if not args:
            await cl.Message(
                content="⚠️ Please specify a provider: `/switch <provider>`\n\nAvailable: openai, anthropic, deepseek",
                author="System",
            ).send()
            return
        
        provider = args.lower().strip()
        available = cl.user_session.get("available_providers", [])
        
        if provider not in available:
            await cl.Message(
                content=f"⚠️ Provider '{provider}' not available or not configured.\n\nAvailable providers: {', '.join(available)}",
                author="System",
            ).send()
            return
        
        try:
            # Get cached model wrapper (or create if first time for this provider)
            model_wrapper = await get_or_create_model_wrapper(provider=provider)
            config = model_wrapper.config
            
            # Update session
            cl.user_session.set("model_wrapper", model_wrapper)
            cl.user_session.set("current_provider", provider)
            
            # Clear history
            cl.user_session.set("conversation_history", [])
            
            await cl.Message(
                content=f"""✅ Switched to **{provider}**

**Model:** {config.model_name}
**Temperature:** {config.temperature}
**Max Tokens:** {config.max_tokens}

Conversation history has been cleared.
""",
                author="System",
            ).send()
        
        except Exception as e:
            logger.error(f"Error switching provider: {str(e)}")
            await cl.Message(
                content=f"❌ Error switching provider: {str(e)}",
                author="System",
            ).send()
    
    else:
        await cl.Message(
            content=f"⚠️ Unknown command: {cmd}\n\nType `/help` for available commands.",
            author="System",
        ).send()


if __name__ == "__main__":
    # This is handled by Chainlit CLI
    pass

