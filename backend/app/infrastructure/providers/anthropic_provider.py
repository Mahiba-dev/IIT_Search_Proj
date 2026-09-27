"""
Infrastructure: Anthropic Claude provider gateway.
"""
from __future__ import annotations

import re

import anthropic
from anthropic import AsyncAnthropic

from app.infrastructure.providers.base import (
    ChatResult,
    InvalidApiKeyError,
    ProviderConnectionError,
    ProviderGateway,
    ProviderRateLimitError,
    ProviderUpstreamError,
)

_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class AnthropicGateway(ProviderGateway):
    def __init__(self, api_key: str, model: str, timeout: float = 30.0):
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout)

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        json_mode: bool = False,
        temperature: float = 0.3,
    ) -> ChatResult:
        effective_system = system_prompt
        if json_mode:
            effective_system += "\n\nRespond with ONLY valid JSON, no markdown code fences, no other text."
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                temperature=temperature,
                system=effective_system,
                messages=[{"role": "user", "content": user_message}],
            )
            text = "".join(block.text for block in response.content if block.type == "text")
            if json_mode:
                text = _CODE_FENCE.sub("", text).strip()
            return ChatResult(text=text, model=self._model)
        except anthropic.AuthenticationError as e:
            raise InvalidApiKeyError("The provided Anthropic API key is invalid or unauthorized.") from e
        except anthropic.RateLimitError as e:
            raise ProviderRateLimitError("Rate limit or quota exceeded. Please try again later.") from e
        except anthropic.APIConnectionError as e:
            raise ProviderConnectionError("Could not reach Anthropic. Check your network and try again.") from e
        except anthropic.APIStatusError as e:
            raise ProviderUpstreamError(f"Anthropic returned an error: {e.message}", e.status_code) from e

    async def validate_key(self) -> bool:
        try:
            await self._client.messages.create(
                model=self._model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except anthropic.AuthenticationError:
            return False
        except Exception:
            return False
