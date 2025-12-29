"""MCP data models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """MCP server configuration.
    
    Attributes:
        name: Server identifier/name
        url: Server URL (for SSE/HTTP connections)
        command: Command to run (for stdio connections)
        args: Command arguments (for stdio connections)
        env: Environment variables (for stdio connections)
        disabled: Whether this server is disabled
    """
    
    name: str
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    disabled: bool = Field(default=False)
    
    class Config:
        """Pydantic config."""
        protected_namespaces = ()


class MCPToolParameter(BaseModel):
    """MCP tool parameter definition.
    
    Attributes:
        type: Parameter type (string, number, boolean, etc.)
        description: Parameter description
        required: Whether parameter is required
        enum: Optional enum values
    """
    
    type: str
    description: Optional[str] = None
    required: bool = Field(default=False)
    enum: Optional[List[str]] = None


class MCPTool(BaseModel):
    """MCP tool definition.
    
    Attributes:
        name: Tool name
        description: Tool description
        inputSchema: Tool input schema (JSON Schema format)
        server_name: Name of the MCP server providing this tool
    """
    
    name: str
    description: Optional[str] = None
    inputSchema: Dict[str, Any] = Field(default_factory=dict)
    server_name: str = Field(default="unknown")
    
    class Config:
        """Pydantic config."""
        protected_namespaces = ()


class MCPToolCall(BaseModel):
    """MCP tool call request.
    
    Attributes:
        name: Tool name to call
        arguments: Tool arguments (dict)
        server_name: Name of the MCP server
    """
    
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    server_name: str = Field(default="unknown")
    
    class Config:
        """Pydantic config."""
        protected_namespaces = ()


class MCPToolResult(BaseModel):
    """MCP tool call result.
    
    Attributes:
        content: Result content (can be string, list, or dict)
        isError: Whether this is an error result
    """
    
    content: Any
    isError: bool = Field(default=False)
    
    class Config:
        """Pydantic config."""
        protected_namespaces = ()

