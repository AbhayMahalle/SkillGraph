"""
LLM Base Provider Interface for SkillGraph.
Defines the standard abstract contract for provider-independent LLM integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass

class LLMConfigurationError(LLMProviderError):
    """Raised when the LLM provider is not configured properly."""
    pass

class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM API request times out."""
    pass

class LLMRateLimitError(LLMProviderError):
    """Raised when an LLM API request is rate-limited (HTTP 429)."""
    pass

class LLMResponseError(LLMProviderError):
    """Raised when an LLM response cannot be parsed or validated."""
    pass

class LLMProvider(ABC):
    """Abstract interface for external LLM providers."""

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Executes a completion request against the LLM provider.
        
        Args:
            system_prompt: System instruction directing model behavior
            user_prompt: User input or structured payload
            json_mode: Whether to enforce JSON output format
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum token limit for output

        Returns:
            Dict containing:
                - "content": Raw or parsed response text/dict
                - "model": Model identifier used
                - "usage": Token usage statistics if provided by API
                - "execution_time": Seconds taken for API round-trip
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the provider is properly configured with credentials and reachable."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Returns metadata about the provider and configured model."""
        pass
