"""Base Agent class and interfaces."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentStep:
    """Represents a single step in Agent execution.
    
    Attributes:
        type: Type of step ('reasoning', 'action', 'observation', 'final')
        content: Content of the step
        metadata: Optional metadata (e.g., tool name, tool input)
    """
    type: str
    content: str
    metadata: Optional[dict[str, Any]] = None


@dataclass
class AgentResult:
    """Result from Agent execution.
    
    Attributes:
        final_answer: The final answer to the user's question
        steps: List of execution steps
        total_iterations: Total number of iterations performed
        token_usage: Optional token usage information
        citations: Optional list of cited sources
    """
    final_answer: str
    steps: list[AgentStep]
    total_iterations: int
    token_usage: Optional[dict[str, int]] = None
    citations: Optional[list[dict[str, str]]] = None


class BaseAgent(ABC):
    """Abstract base class for all agents.
    
    This class defines the interface that all agent implementations must follow.
    """
    
    @abstractmethod
    async def run(self, user_input: str) -> AgentResult:
        """Run the agent on user input.
        
        Args:
            user_input: User's question or request
            
        Returns:
            AgentResult containing the final answer and execution steps
            
        Raises:
            TimeoutError: If execution exceeds max_execution_time
            RuntimeError: If agent fails to complete
        """
        pass
    
    @abstractmethod
    async def stream(self, user_input: str) -> AsyncIterator[AgentStep]:
        """Stream agent execution steps in real-time.
        
        Args:
            user_input: User's question or request
            
        Yields:
            AgentStep objects as they are generated
            
        Raises:
            TimeoutError: If execution exceeds max_execution_time
            RuntimeError: If agent fails to complete
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset agent state (clear history, cache, etc.)."""
        pass


class AgentError(Exception):
    """Base exception for Agent errors."""
    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""
    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass


class AgentIterationLimitError(AgentError):
    """Raised when agent exceeds max iterations."""
    pass

