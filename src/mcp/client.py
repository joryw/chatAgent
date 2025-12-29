"""MCP Client implementation for connecting to MCP servers."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

try:
    from mcp.client.session import ClientSession
    from mcp.client.sse import sse_client
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("MCP SDK not available, using custom implementation")

from .models import MCPServerConfig, MCPTool, MCPToolCall, MCPToolResult

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client for connecting to MCP servers.
    
    Supports both HTTP and SSE (Server-Sent Events) connection modes.
    
    Attributes:
        config: MCP server configuration
        base_url: Base URL for HTTP connections
        tools: Discovered tools from the server
        _client: HTTP client instance
    """
    
    def __init__(self, config: MCPServerConfig):
        """Initialize MCP Client.
        
        Args:
            config: MCP server configuration
        """
        self.config = config
        self.base_url = config.url or ""
        self.tools: List[MCPTool] = []
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        
        logger.info(f"初始化 MCP Client: {config.name} (URL: {self.base_url})")
    
    async def initialize(self) -> bool:
        """Initialize connection to MCP server and discover tools.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
        
        if self.config.disabled:
            logger.info(f"⏭️  MCP 服务器 {self.config.name} 已禁用，跳过初始化")
            return False
        
        try:
            # Create HTTP client
            timeout = httpx.Timeout(10.0, connect=5.0)
            self._client = httpx.AsyncClient(timeout=timeout)
            
            # Discover tools
            await self._discover_tools()
            
            self._initialized = True
            logger.info(f"✅ MCP Client {self.config.name} 初始化成功，发现 {len(self.tools)} 个工具")
            return True
            
        except Exception as e:
            logger.error(f"❌ MCP Client {self.config.name} 初始化失败: {e}", exc_info=True)
            return False
    
    async def _discover_tools(self) -> None:
        """Discover available tools from MCP server.
        
        For SSE endpoints, we'll try to call the tools/list endpoint.
        For HTTP endpoints, we'll use the standard MCP protocol.
        """
        try:
            if "/sse" in self.base_url.lower():
                # SSE endpoint - try to get tools via HTTP GET/POST
                await self._discover_tools_sse()
            else:
                # Standard HTTP endpoint
                await self._discover_tools_http()
        except Exception as e:
            logger.warning(f"⚠️ 工具发现失败 ({self.config.name}): {e}")
            # Don't fail initialization if tool discovery fails
            self.tools = []
    
    async def _discover_tools_sse(self) -> None:
        """Discover tools from SSE endpoint using MCP SDK.
        
        Uses MCP SDK's ClientSession to properly handle SSE endpoints.
        """
        if not MCP_SDK_AVAILABLE:
            logger.warning("⚠️ MCP SDK 不可用，无法发现 SSE 端点工具")
            self.tools = []
            return
        
        try:
            # Use MCP SDK's sse_client to connect to SSE endpoint
            from mcp.client.sse import sse_client
            
            # Connect to SSE endpoint using full URL (includes query params)
            async with sse_client(self.base_url) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize session
                    await session.initialize()
                    
                    # List tools
                    tools_result = await session.list_tools()
                    
                    if tools_result and tools_result.tools:
                        self.tools = [
                            MCPTool(
                                name=tool.name,
                                description=tool.description or "",
                                inputSchema=tool.inputSchema.model_dump() if hasattr(tool.inputSchema, 'model_dump') else (tool.inputSchema if isinstance(tool.inputSchema, dict) else {}),
                                server_name=self.config.name,
                            )
                            for tool in tools_result.tools
                        ]
                        logger.info(f"✅ 通过 MCP SDK 发现 {len(self.tools)} 个工具")
                    else:
                        logger.warning("⚠️ MCP SDK 未返回任何工具")
                        self.tools = []
                        
        except Exception as e:
            logger.error(f"❌ 使用 MCP SDK 发现 SSE 工具失败: {e}", exc_info=True)
            # Fallback: try direct HTTP request
            await self._discover_tools_sse_fallback()
    
    async def _discover_tools_sse_fallback(self) -> None:
        """Fallback method to discover tools from SSE endpoint via direct HTTP.
        
        This is a fallback when MCP SDK is not available or fails.
        """
        if not self._client:
            return
        
        try:
            # Try direct HTTP GET to the SSE endpoint with Accept: text/event-stream
            # Some SSE endpoints may return tool list on initial connection
            response = await self._client.get(
                self.base_url,
                headers={
                    "Accept": "text/event-stream, application/json",
                    "Cache-Control": "no-cache",
                },
                timeout=5.0,
            )
            
            # If it's JSON response, try to parse
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = response.json()
                    if "tools" in data:
                        self.tools = [
                            MCPTool(
                                name=tool.get("name", ""),
                                description=tool.get("description"),
                                inputSchema=tool.get("inputSchema", {}),
                                server_name=self.config.name,
                            )
                            for tool in data["tools"]
                        ]
                        return
        except Exception as e:
            logger.debug(f"SSE fallback discovery failed: {e}")
        
        logger.info(f"📋 SSE 端点工具发现失败，将在调用时动态发现")
        self.tools = []
    
    async def _discover_tools_http(self) -> None:
        """Discover tools from HTTP endpoint."""
        if not self._client:
            return
        
        try:
            # Standard MCP tools/list request
            response = await self._client.post(
                f"{self.base_url}/tools/list",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "tools" in data["result"]:
                    self.tools = [
                        MCPTool(
                            name=tool.get("name", ""),
                            description=tool.get("description"),
                            inputSchema=tool.get("inputSchema", {}),
                            server_name=self.config.name,
                        )
                        for tool in data["result"]["tools"]
                    ]
        except Exception as e:
            logger.warning(f"⚠️ HTTP 工具发现失败: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            MCPToolResult with tool execution result
            
        Raises:
            Exception: If tool call fails
        """
        if not self._client:
            raise RuntimeError(f"MCP Client {self.config.name} not initialized")
        
        try:
            logger.info(f"🔧 调用 MCP 工具: {tool_name} (服务器: {self.config.name})")
            
            if "/sse" in self.base_url.lower():
                # SSE endpoint - use HTTP POST
                result = await self._call_tool_sse(tool_name, arguments)
            else:
                # Standard HTTP endpoint
                result = await self._call_tool_http(tool_name, arguments)
            
            logger.info(f"✅ MCP 工具调用成功: {tool_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ MCP 工具调用失败 ({tool_name}): {e}", exc_info=True)
            return MCPToolResult(
                content=f"工具调用失败: {str(e)}",
                isError=True,
            )
    
    async def _call_tool_sse(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call tool via SSE endpoint using MCP SDK."""
        if not MCP_SDK_AVAILABLE:
            return MCPToolResult(
                content="MCP SDK 不可用，无法调用 SSE 端点工具",
                isError=True,
            )
        
        try:
            # Use MCP SDK's sse_client to connect to SSE endpoint
            from mcp.client.sse import sse_client
            
            # Connect to SSE endpoint using full URL (includes query params)
            async with sse_client(self.base_url) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize session
                    await session.initialize()
                    
                    # Call tool
                    result = await session.call_tool(tool_name, arguments)
                    
                    # Check if result has error
                    if result.isError:
                        error_msg = "工具调用错误"
                        if hasattr(result, 'error') and result.error:
                            if isinstance(result.error, dict):
                                error_msg = result.error.get("message", error_msg)
                            else:
                                error_msg = str(result.error)
                        return MCPToolResult(content=error_msg, isError=True)
                    
                    # Extract content from result
                    # result.content is a list of content items (TextContent, ImageContent, etc.)
                    content_parts = []
                    if result.content:
                        for item in result.content:
                            # Handle different content types
                            if hasattr(item, 'text'):
                                # TextContent object (has .text attribute)
                                content_parts.append(item.text)
                            elif hasattr(item, 'model_dump'):
                                # Pydantic model, convert to dict
                                try:
                                    item_dict = item.model_dump()
                                    if "text" in item_dict:
                                        content_parts.append(item_dict["text"])
                                    elif "type" in item_dict:
                                        # Handle other content types (image, audio, etc.)
                                        content_parts.append(f"[{item_dict.get('type', 'unknown')} content]")
                                    else:
                                        content_parts.append(str(item_dict))
                                except Exception:
                                    content_parts.append(str(item))
                            elif isinstance(item, dict):
                                # Dictionary
                                if "text" in item:
                                    content_parts.append(item["text"])
                                elif "type" in item:
                                    content_parts.append(f"[{item.get('type', 'unknown')} content]")
                                else:
                                    content_parts.append(str(item))
                            else:
                                # String or other type
                                content_parts.append(str(item))
                    
                    # Also check structuredContent if available
                    if result.structuredContent:
                        try:
                            import json
                            structured_str = json.dumps(result.structuredContent, ensure_ascii=False, indent=2)
                            content_parts.append(f"\n结构化数据:\n{structured_str}")
                        except Exception:
                            pass
                    
                    content = "\n".join(content_parts) if content_parts else "工具调用成功，但未返回内容"
                    return MCPToolResult(content=content, isError=False)
                        
        except Exception as e:
            logger.error(f"❌ 使用 MCP SDK 调用 SSE 工具失败: {e}", exc_info=True)
            return MCPToolResult(
                content=f"工具调用失败: {str(e)}",
                isError=True,
            )
    
    async def _call_tool_http(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Call tool via HTTP endpoint."""
        if not self._client:
            raise RuntimeError("Client not initialized")
        
        response = await self._client.post(
            f"{self.base_url}/tools/call",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
                "id": 1,
            },
            headers={"Content-Type": "application/json"},
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                content = data["result"].get("content", [])
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
                    return MCPToolResult(content=text_content, isError=False)
                return MCPToolResult(content=str(data["result"]), isError=False)
            elif "error" in data:
                return MCPToolResult(
                    content=f"工具调用错误: {data['error'].get('message', 'Unknown error')}",
                    isError=True,
                )
        
        return MCPToolResult(
            content=f"HTTP 请求失败: {response.status_code}",
            isError=True,
        )
    
    async def close(self) -> None:
        """Close the MCP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._initialized = False
            logger.info(f"🔌 MCP Client {self.config.name} 已关闭")
    
    def __del__(self):
        """Cleanup on deletion."""
        if self._client:
            # Note: Can't use async in __del__, so we'll rely on explicit close()
            pass

