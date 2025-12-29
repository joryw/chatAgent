"""MCP Tool to LangChain Tool adapter."""

import logging
from typing import Any, Dict, List, Optional, Type
import json

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, create_model

from .client import MCPClient
from .models import MCPTool, MCPToolResult

logger = logging.getLogger(__name__)


class MCPToolAdapter(BaseTool):
    """Adapter that wraps MCP tools as LangChain tools.
    
    This adapter converts MCP tool definitions into LangChain Tool instances
    that can be used by agents.
    
    Attributes:
        name: Tool name
        description: Tool description
        args_schema: Input schema (dynamically created from MCP tool schema)
        mcp_client: MCP Client instance
        mcp_tool: Original MCP tool definition
    """
    
    mcp_client: MCPClient = Field(exclude=True)
    mcp_tool: MCPTool = Field(exclude=True)
    
    def __init__(self, mcp_client: MCPClient, mcp_tool: MCPTool, **kwargs):
        """Initialize MCP Tool Adapter.
        
        Args:
            mcp_client: MCP Client instance
            mcp_tool: MCP tool definition
            **kwargs: Additional arguments for BaseTool
        """
        # Create dynamic input schema from MCP tool's inputSchema
        args_schema = self._create_input_schema(mcp_tool)
        
        super().__init__(
            name=mcp_tool.name,
            description=mcp_tool.description or f"MCP tool: {mcp_tool.name}",
            args_schema=args_schema,
            mcp_client=mcp_client,
            mcp_tool=mcp_tool,
            **kwargs
        )
    
    def _create_input_schema(self, mcp_tool: MCPTool) -> Type[BaseModel]:
        """Create Pydantic input schema from MCP tool's JSON Schema.
        
        Args:
            mcp_tool: MCP tool definition
            
        Returns:
            Pydantic model class for tool inputs
        """
        input_schema = mcp_tool.inputSchema
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        # Create field definitions
        field_definitions: Dict[str, Any] = {}
        
        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            prop_description = prop_schema.get("description", "")
            is_required = prop_name in required
            
            # Map JSON Schema types to Python types
            if prop_type == "string":
                field_type = str
            elif prop_type == "number" or prop_type == "integer":
                field_type = float if prop_type == "number" else int
            elif prop_type == "boolean":
                field_type = bool
            elif prop_type == "array":
                field_type = list
            elif prop_type == "object":
                field_type = dict
            else:
                field_type = str  # Default to string
            
            # Create Field with description
            field_definitions[prop_name] = (
                field_type if is_required else Optional[field_type],
                Field(
                    default=None if not is_required else ...,
                    description=prop_description,
                ),
            )
        
        # If no properties, create a simple schema with a generic input
        if not field_definitions:
            field_definitions["input"] = (
                str,
                Field(description="Tool input"),
            )
        
        # Create dynamic model class
        model_name = f"{mcp_tool.name.title().replace('_', '')}Input"
        return create_model(model_name, **field_definitions)
    
    def _run(self, **kwargs: Any) -> str:
        """Execute tool synchronously.
        
        Note: This method uses asyncio.run to execute async operations.
        For better performance, use _arun instead.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        import asyncio
        
        try:
            # Remove None values
            clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            # Run async call
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    logger.warning("⚠️ 同步调用在异步上下文中，应该使用 _arun 方法")
                    return "工具调用需要在异步上下文中使用。请使用异步方法。"
            except RuntimeError:
                pass
            
            result = asyncio.run(self.mcp_client.call_tool(self.mcp_tool.name, clean_kwargs))
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"❌ MCP 工具执行失败 ({self.mcp_tool.name}): {e}", exc_info=True)
            return f"工具执行失败: {str(e)}"
    
    async def _arun(self, **kwargs: Any) -> str:
        """Execute tool asynchronously.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        try:
            # Remove None values
            clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            logger.info(f"🔧 调用 MCP 工具: {self.mcp_tool.name} (参数: {clean_kwargs})")
            result = await self.mcp_client.call_tool(self.mcp_tool.name, clean_kwargs)
            
            formatted = self._format_result(result)
            logger.info(f"✅ MCP 工具调用完成: {self.mcp_tool.name}")
            return formatted
            
        except Exception as e:
            logger.error(f"❌ MCP 工具执行失败 ({self.mcp_tool.name}): {e}", exc_info=True)
            return f"工具执行失败: {str(e)}"
    
    def _format_result(self, result: MCPToolResult) -> str:
        """Format tool result for Agent consumption.
        
        Args:
            result: MCPToolResult instance
            
        Returns:
            Formatted string result
        """
        if result.isError:
            return f"❌ 错误: {result.content}"
        
        # Format content based on type
        if isinstance(result.content, str):
            return result.content
        elif isinstance(result.content, dict):
            # Try to format as JSON
            try:
                return json.dumps(result.content, ensure_ascii=False, indent=2)
            except Exception:
                return str(result.content)
        elif isinstance(result.content, list):
            # Format list items
            formatted_items = []
            for item in result.content:
                if isinstance(item, dict):
                    formatted_items.append(json.dumps(item, ensure_ascii=False))
                else:
                    formatted_items.append(str(item))
            return "\n".join(formatted_items)
        else:
            return str(result.content)
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


def create_mcp_tools(mcp_clients: List[MCPClient]) -> List[BaseTool]:
    """Create LangChain tools from MCP clients.
    
    Args:
        mcp_clients: List of initialized MCP clients
        
    Returns:
        List of LangChain Tool instances
    """
    tools: List[BaseTool] = []
    
    for client in mcp_clients:
        if not client._initialized:
            continue
        
        for mcp_tool in client.tools:
            try:
                adapter = MCPToolAdapter(mcp_client=client, mcp_tool=mcp_tool)
                tools.append(adapter)
                logger.info(f"✅ 注册 MCP 工具: {mcp_tool.name} (服务器: {client.config.name})")
            except Exception as e:
                logger.error(f"❌ 创建 MCP 工具适配器失败 ({mcp_tool.name}): {e}", exc_info=True)
    
    logger.info(f"📦 共注册 {len(tools)} 个 MCP 工具")
    return tools

