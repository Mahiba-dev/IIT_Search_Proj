"""
Infrastructure layer: the common interface every AI provider integration
implements (this is the "IAIProviderService" equivalent from the spec).
The application layer depends only on this interface, never on a specific
provider's SDK, so new providers can be added without touching validation
or search orchestration logic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderError(Exception):
    """Base class for translated, user-safe provider errors."""


class InvalidApiKeyError(ProviderError):
    pass


class ProviderRateLimitError(ProviderError):
    pass


class ProviderConnectionError(ProviderError):
    pass


class ProviderUpstreamError(ProviderError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class UnsupportedProviderConfigError(ProviderError):
    """Raised when required config (e.g. base_url for a custom provider) is missing."""


@dataclass
class ChatResult:
    text: str
    model: str


class ProviderGateway(ABC):
    """Common interface implemented by every AI provider integration."""

    @abstractmethod
    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        json_mode: bool = False,
        temperature: float = 0.3,
    ) -> ChatResult:
        """Send a single-turn chat completion request and return the text response."""
        raise NotImplementedError

    @abstractmethod
    async def validate_key(self) -> bool:
        """Lightweight call used to confirm the API key is valid for this provider."""
        raise NotImplementedError
