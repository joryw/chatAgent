"""Main Chainlit application for AI Agent with Model Invocation."""

import asyncio
import logging
import os
from typing import Optional

import chainlit as cl
from chainlit.input_widget import Switch
from dotenv import load_dotenv

from src.config.model_config import (
    ModelProvider,
    get_model_config,
    get_available_providers,
)
from src.config.search_config import get_search_config, is_search_available
from src.models.factory import get_model_wrapper
from src.prompts.templates import (
    DEFAULT_SYSTEM_MESSAGE,
    count_prompt_tokens,
    build_system_message_with_search,
)
from src.search.search_service import SearchService

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
        search_enabled = settings.get("web_search", False)
        search_service = cl.user_session.get("search_service")
        
        if search_service:
            # Update search enabled state
            cl.user_session.set("search_enabled", search_enabled)
            
            # Send confirmation message
            status = "✅ 已启用" if search_enabled else "❌ 已禁用"
            await cl.Message(
                content=f"联网搜索 {status}",
                author="System",
            ).send()
        else:
            # Search service not available
            await cl.Message(
                content="⚠️ 搜索服务不可用，无法启用联网搜索。\n\n请检查 SearXNG 配置。",
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
            
            # Store in session
            cl.user_session.set("model_wrapper", model_wrapper)
            cl.user_session.set("current_provider", default_provider)
            cl.user_session.set("available_providers", available_providers)
            cl.user_session.set("conversation_history", [])
            cl.user_session.set("search_service", search_service)
            cl.user_session.set("search_enabled", False)  # Default off
            
            # Prepare welcome message first
            if search_available and search_service:
                search_status = "✅ 可用 (本地部署)"
                search_hint = ""
            else:
                search_status = "❌ 不可用"
                search_hint = "\n\n💡 **启用联网搜索:**\n1. 部署 SearXNG: `docs/guides/searxng-deployment.md`\n2. 配置 `.env`: `SEARXNG_URL=http://localhost:8080`\n3. 重启应用\n"
            
            welcome_msg = f"""# 🤖 Welcome to AI Agent Chat!

**Current Model:** {config.model_name}
**Provider:** {config.provider}
**Temperature:** {config.temperature}
**Max Tokens:** {config.max_tokens}

**Available Providers:** {', '.join(available_providers)}
**联网搜索:** {search_status}{search_hint}

You can start chatting now! Type your message below.

**💡 使用 UI 开关:**
- 点击右上角 ⚙️ 图标打开设置面板
- 切换 "🔍 联网搜索" 开关即可启用/禁用搜索功能
- 开关状态会立即生效

**Commands (备用方式):**
- `/switch <provider>` - Switch to a different model provider
- `/search <on|off>` - Enable or disable web search (also via UI toggle)
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
            
            chat_settings = cl.ChatSettings(
                [
                    Switch(
                        id="web_search",
                        label="🔍 联网搜索",
                        initial=False,
                        description="启用后将使用 SearXNG 搜索实时信息",
                        disabled=(search_service is None),
                    )
                ]
            )
            
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
        
        # Create response message
        response_msg = cl.Message(
            content="",
            author="Assistant",
        )
        await response_msg.send()
        
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
            
            # Generate streaming response
            full_response = ""
            async for chunk in model_wrapper.generate_stream(
                prompt=user_message,
                system_message=system_message,
            ):
                full_response += chunk.content
                response_msg.content = full_response
                await response_msg.update()
            
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
            response_msg.content = f"❌ Error generating response: {str(e)}\n\nPlease try again."
            await response_msg.update()
    
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
        help_msg = """# 📖 Available Commands

**💡 推荐使用 UI 开关:**
- 点击右上角 ⚙️ 图标打开设置面板
- 直接切换 "🔍 联网搜索" 开关

**命令列表 (备用方式):**
- `/switch <provider>` - Switch to a different model provider (openai, anthropic, deepseek)
- `/search <on|off>` - Enable or disable web search (推荐使用UI开关)
- `/config` - View current configuration
- `/reset` - Clear conversation history
- `/help` - Show this help message

**Examples:**
```
/switch deepseek
/search on
/search off
```
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
        search_status = "✅ Enabled" if search_enabled else "❌ Disabled"
        if not search_service:
            search_status = "⚠️ Not Available"
        
        config_msg = f"""# ⚙️ Current Configuration

**Provider:** {config.provider}
**Model:** {config.model_name}
**Temperature:** {config.temperature}
**Max Tokens:** {config.max_tokens}
**Top P:** {config.top_p}
**Timeout:** {config.timeout}s

**Web Search:** {search_status}

**Available Providers:** {', '.join(cl.user_session.get('available_providers', []))}

💡 **提示:** 可通过右上角 ⚙️ 设置面板切换联网搜索开关
"""
        await cl.Message(content=config_msg, author="System").send()
    
    elif cmd == "/reset":
        cl.user_session.set("conversation_history", [])
        await cl.Message(
            content="✅ Conversation history cleared.",
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

