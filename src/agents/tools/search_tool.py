"""Search tool for LangChain Agent."""

import logging
from typing import Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.search.search_service import SearchService
from src.search.models import SearchResult

logger = logging.getLogger(__name__)


class SearchInput(BaseModel):
    """Input schema for search tool."""
    
    query: str = Field(
        description="搜索查询关键词。应该具体、清晰、针对性强，以获取最相关的信息。"
    )


class SearchTool(BaseTool):
    """Web search tool for Agent.
    
    This tool wraps SearchService to provide web search capability to LangChain agents.
    It searches the internet for real-time information when needed.
    
    Attributes:
        name: Tool name
        description: Tool description for Agent to understand when to use it
        args_schema: Input schema (Pydantic model)
        search_service: SearchService instance
        return_direct: Whether to return result directly (False for Agent)
    """
    
    name: str = "web_search"
    description: str = (
        "搜索互联网获取实时信息。"
        "当需要了解最新事件、实时数据、当前新闻或验证信息时使用此工具。"
        "输入应该是一个清晰、具体的搜索查询。"
        "例如: '2024年人工智能最新进展', 'OpenAI GPT-4 Turbo 发布时间'"
    )
    args_schema: Type[BaseModel] = SearchInput
    search_service: SearchService = Field(exclude=True)
    return_direct: bool = False
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
    
    def _run(self, query: str) -> str:
        """Execute search synchronously.
        
        Note: SearchService uses async operations, so this method uses asyncio.run
        to execute the async search. For better performance, use _arun instead.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted search results as string
        """
        import asyncio
        try:
            logger.info(f"🔍 Agent 调用搜索工具 (同步): {query}")
            # SearchService.search is async, so we need to run it in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we can't use run()
                    # This shouldn't happen in LangChain Agent, but handle it gracefully
                    logger.warning("⚠️ 同步调用在异步上下文中，应该使用 _arun 方法")
                    return "搜索工具需要在异步上下文中使用。请使用异步方法。"
            except RuntimeError:
                # No event loop running, we can create one
                pass
            
            # Run async search synchronously
            search_response = asyncio.run(self.search_service.search(query))
            
            if not search_response or search_response.is_empty():
                return "未找到相关搜索结果。请尝试使用不同的关键词或基于已有知识回答。"
            
            # Extract results from SearchResponse
            results = search_response.results if search_response.results else []
            
            if not results:
                return "未找到相关搜索结果。请尝试使用不同的关键词或基于已有知识回答。"
            
            # Format results for Agent
            formatted = self._format_results(results)
            logger.info(f"✅ 搜索完成，找到 {len(results)} 条结果")
            return formatted
            
        except Exception as e:
            logger.error(f"❌ 搜索工具执行失败: {e}", exc_info=True)
            return f"搜索失败: {str(e)}。请尝试重新搜索或基于已有知识回答。"
    
    async def _arun(self, query: str) -> str:
        """Execute search asynchronously.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted search results as string
        """
        try:
            logger.info(f"🔍 Agent 调用搜索工具 (异步): {query}")
            # SearchService.search is already async, use it directly
            search_response = await self.search_service.search(query)
            
            if not search_response or search_response.is_empty():
                return "未找到相关搜索结果。请尝试使用不同的关键词或基于已有知识回答。"
            
            # Extract results from SearchResponse
            results = search_response.results if search_response.results else []
            
            if not results:
                return "未找到相关搜索结果。请尝试使用不同的关键词或基于已有知识回答。"
            
            # Format results for Agent
            formatted = self._format_results(results)
            logger.info(f"✅ 搜索完成，找到 {len(results)} 条结果")
            return formatted
            
        except Exception as e:
            logger.error(f"❌ 搜索工具执行失败: {e}", exc_info=True)
            return f"搜索失败: {str(e)}。请尝试重新搜索或基于已有知识回答。"
    
    def _format_results(self, results: list[SearchResult]) -> str:
        """Format search results for Agent consumption.
        
        Args:
            results: List of SearchResult objects
            
        Returns:
            Formatted string with numbered results
        """
        formatted_parts = ["搜索结果:\n"]
        
        for i, result in enumerate(results, 1):
            # Truncate content to 200 characters
            content = result.content[:200] + "..." if len(result.content) > 200 else result.content
            
            formatted_parts.append(
                f"[{i}] {result.title}\n"
                f"来源: {result.url}\n"
                f"摘要: {content}\n"
            )
        
        formatted_parts.append(
            f"\n找到 {len(results)} 条搜索结果。"
            f"你可以使用 [数字] 格式在回答中引用这些来源。"
        )
        
        return "\n".join(formatted_parts)


def create_search_tool(search_service: SearchService) -> SearchTool:
    """Create a search tool instance.
    
    Args:
        search_service: SearchService instance
        
    Returns:
        SearchTool instance ready to use
    """
    return SearchTool(search_service=search_service)

