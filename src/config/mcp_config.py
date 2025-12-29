"""MCP configuration management.

MCP configuration is loaded from project-local configuration file only.
Configuration file location: <project_root>/mcp.json
"""

import json
from typing import List
from pathlib import Path

from src.mcp.models import MCPServerConfig

logger = None


def _get_logger():
    """Lazy import logger to avoid circular imports."""
    global logger
    if logger is None:
        import logging
        logger = logging.getLogger(__name__)
    return logger


def _get_project_root() -> Path:
    """Get project root directory.
    
    Assumes this file is in src/config/, so project root is 2 levels up.
    
    Returns:
        Path to project root directory
    """
    # This file is in src/config/mcp_config.py
    # Project root is 2 levels up
    current_file = Path(__file__)
    return current_file.parent.parent.parent


class MCPConfig:
    """MCP configuration manager.
    
    Loads configuration from project-local file: <project_root>/mcp.json
    """
    
    @staticmethod
    def load_from_file(file_path: str = None) -> List[MCPServerConfig]:
        """Load MCP server configurations from project-local JSON file.
        
        Default file path: <project_root>/mcp.json
        
        Args:
            file_path: Optional custom file path (relative to project root or absolute)
            
        Returns:
            List of MCP server configurations
        """
        log = _get_logger()
        servers: List[MCPServerConfig] = []
        
        # Determine file path
        if file_path is None:
            project_root = _get_project_root()
            file_path = project_root / "mcp.json"
        else:
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                # Relative path - resolve from project root
                project_root = _get_project_root()
                file_path = project_root / file_path
            else:
                file_path = file_path_obj
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            log.debug(f"MCP 配置文件不存在: {file_path}")
            return servers
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            mcp_servers = data.get("mcpServers", {})
            
            for server_name, server_config in mcp_servers.items():
                try:
                    # Handle disabled flag
                    disabled = server_config.get("disabled", False)
                    
                    config = MCPServerConfig(
                        name=server_name,
                        url=server_config.get("url"),
                        command=server_config.get("command"),
                        args=server_config.get("args"),
                        env=server_config.get("env"),
                        disabled=disabled,
                    )
                    
                    servers.append(config)
                    log.debug(f"✅ 从项目配置文件加载 MCP 服务器: {server_name}")
                    
                except Exception as e:
                    log.error(f"❌ 解析 MCP 服务器配置失败 ({server_name}): {e}", exc_info=True)
            
        except json.JSONDecodeError as e:
            log.error(f"❌ MCP 配置文件 JSON 格式错误 ({file_path}): {e}", exc_info=True)
        except Exception as e:
            log.error(f"❌ 读取 MCP 配置文件失败 ({file_path}): {e}", exc_info=True)
        
        return servers
    
    @staticmethod
    def get_all_configs() -> List[MCPServerConfig]:
        """Get all MCP server configurations from project-local file.
        
        Returns:
            List of MCP server configurations
        """
        log = _get_logger()
        servers = MCPConfig.load_from_file()
        
        if servers:
            log.info(f"📋 从项目配置文件加载了 {len(servers)} 个 MCP 服务器配置")
        else:
            log.debug("📋 未找到 MCP 服务器配置（配置文件不存在或为空）")
        
        return servers


def get_mcp_configs() -> List[MCPServerConfig]:
    """Get MCP server configurations from project-local file.
    
    Returns:
        List of MCP server configurations
    """
    return MCPConfig.get_all_configs()


def is_mcp_available() -> bool:
    """Check if MCP functionality is available.
    
    Returns:
        True if at least one MCP server is configured and not disabled
    """
    configs = get_mcp_configs()
    enabled_configs = [c for c in configs if not c.disabled]
    return len(enabled_configs) > 0

