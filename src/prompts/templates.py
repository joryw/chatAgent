"""Prompt template management and formatting utilities."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Template for prompt construction.
    
    Attributes:
        template: Template string with {variable} placeholders
        system_message: Optional system message template
        required_variables: List of required variable names
    """
    
    template: str
    system_message: Optional[str] = None
    required_variables: list[str] = None
    
    def __post_init__(self):
        """Extract required variables from template."""
        if self.required_variables is None:
            self.required_variables = self._extract_variables(self.template)
            if self.system_message:
                self.required_variables.extend(
                    self._extract_variables(self.system_message)
                )
    
    @staticmethod
    def _extract_variables(template: str) -> list[str]:
        """Extract variable names from template string.
        
        Args:
            template: Template string with {variable} placeholders
        
        Returns:
            List of variable names
        """
        import re
        return list(set(re.findall(r'\{(\w+)\}', template)))
    
    def format(self, **kwargs) -> tuple[str, Optional[str]]:
        """Format template with provided variables.
        
        Args:
            **kwargs: Variable values for template
        
        Returns:
            Tuple of (formatted_prompt, formatted_system_message)
        
        Raises:
            ValueError: If required variables are missing
        """
        # Check for missing variables
        missing = set(self.required_variables) - set(kwargs.keys())
        if missing:
            raise ValueError(
                f"Missing required variables: {', '.join(missing)}"
            )
        
        # Format prompt
        try:
            formatted_prompt = self.template.format(**kwargs)
            formatted_system = None
            
            if self.system_message:
                formatted_system = self.system_message.format(**kwargs)
            
            return formatted_prompt, formatted_system
        
        except KeyError as e:
            raise ValueError(f"Invalid variable in template: {e}")
    
    def validate(self, **kwargs) -> bool:
        """Validate that all required variables are provided.
        
        Args:
            **kwargs: Variable values to validate
        
        Returns:
            True if all required variables are present
        """
        return all(var in kwargs for var in self.required_variables)


def format_prompt(
    template: str,
    variables: Dict[str, Any],
    system_message: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """Format a prompt template with variables.
    
    Args:
        template: Template string with {variable} placeholders
        variables: Dictionary of variable values
        system_message: Optional system message template
    
    Returns:
        Tuple of (formatted_prompt, formatted_system_message)
    
    Example:
        >>> prompt, system = format_prompt(
        ...     "Tell me about {topic}",
        ...     {"topic": "Python"},
        ...     "You are a helpful assistant."
        ... )
    """
    prompt_template = PromptTemplate(
        template=template,
        system_message=system_message,
    )
    return prompt_template.format(**variables)


def count_prompt_tokens(
    prompt: str,
    system_message: Optional[str] = None,
    encoding: str = "cl100k_base",
) -> int:
    """Count tokens in a prompt.
    
    Args:
        prompt: User prompt text
        system_message: Optional system message
        encoding: Tiktoken encoding to use (default: cl100k_base for GPT-4)
    
    Returns:
        Total number of tokens
    
    Example:
        >>> tokens = count_prompt_tokens("Hello, world!")
        >>> print(tokens)  # Approximately 4 tokens
    """
    try:
        tokenizer = tiktoken.get_encoding(encoding)
    except KeyError:
        logger.warning(f"Unknown encoding {encoding}, using cl100k_base")
        tokenizer = tiktoken.get_encoding("cl100k_base")
    
    # Count tokens for each message
    # Add overhead for message formatting (role, delimiters, etc.)
    tokens = 0
    
    if system_message:
        tokens += len(tokenizer.encode(system_message))
        tokens += 4  # Overhead for system message
    
    tokens += len(tokenizer.encode(prompt))
    tokens += 4  # Overhead for user message
    tokens += 3  # Overhead for assistant response priming
    
    return tokens


# Common prompt templates
DEFAULT_SYSTEM_MESSAGE = """You are a helpful AI assistant. 
You provide accurate, concise, and useful responses to user queries.
You are respectful, honest, and strive to be helpful."""


def build_system_message_with_search(
    base_message: str,
    search_results: Optional[str] = None,
) -> str:
    """Build system message with optional search results.
    
    Args:
        base_message: Base system message
        search_results: Formatted search results to inject
    
    Returns:
        Complete system message with search results if provided
    """
    if not search_results:
        return base_message
    
    return f"""{base_message}

{search_results}

重要提示：
- 在回答时，请优先参考上述搜索结果中的信息
- 如果引用搜索结果，请使用 [数字] 标记来源（如 [1]、[2]）
- 如果搜索结果与你的知识有冲突，请说明并解释差异
- 如果搜索结果不足以回答问题，可以结合你的知识补充"""


CONVERSATIONAL_TEMPLATE = PromptTemplate(
    template="{user_message}",
    system_message=DEFAULT_SYSTEM_MESSAGE,
    required_variables=["user_message"],
)


TASK_ORIENTED_TEMPLATE = PromptTemplate(
    template="""Task: {task_description}

Context: {context}

Please provide a detailed response.""",
    system_message="""You are a task-oriented AI assistant.
You break down tasks into clear steps and provide actionable guidance.""",
    required_variables=["task_description", "context"],
)


QA_TEMPLATE = PromptTemplate(
    template="""Question: {question}

Please provide a clear and accurate answer.""",
    system_message="""You are a knowledgeable assistant that provides 
accurate answers to questions. You cite sources when appropriate and 
acknowledge when you're uncertain.""",
    required_variables=["question"],
)

