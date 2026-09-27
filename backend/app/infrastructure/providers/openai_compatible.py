"""
Infrastructure: OpenAI-compatible gateway.

OpenAI, Mistral, Groq, DeepSeek, OpenRouter, and any "custom OpenAI-compatible"
endpoint all speak the same /chat/completions request/response shape, so a
single implementation (parameterized by base_url) covers all of them. Each
provider factory function below just supplies the right base_url and
provider-specific quirks (e.g. OpenRouter recommends extra headers).
"""
from __future__ import annotations

from typing import Optional

from openai import (
    AsyncOpenAI,
    AuthenticationError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

from app.infrastructure.providers.base import (
    ChatResult,
    InvalidApiKeyError,
    ProviderConnectionError,
    ProviderGateway,
    ProviderRateLimitError,
    ProviderUpstreamError,
)


class OpenAICompatibleGateway(ProviderGateway):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        extra_headers: Optional[dict] = None,
    ):
        self._model = model
        self._extra_headers = extra_headers or {}
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        json_mode: bool = False,
        temperature: float = 0.3,
    ) -> ChatResult:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        try:
            return await self._call(messages, temperature, json_mode)
        except APIStatusError as e:
            if json_mode and e.status_code == 400:
                # Some OpenAI-compatible providers (esp. via OpenRouter, or
                # smaller models) reject response_format=json_object. Retry
                # once without it; the prompts already ask for JSON-only output.
                try:
                    return await self._call(messages, temperature, json_mode=False)
                except APIStatusError as e2:
                    raise ProviderUpstreamError(f"Upstream error: {e2.message}", e2.status_code) from e2
            raise ProviderUpstreamError(f"Upstream error: {e.message}", e.status_code) from e
        except AuthenticationError as e:
            raise InvalidApiKeyError("The provided API key is invalid or unauthorized.") from e
        except RateLimitError as e:
            raise ProviderRateLimitError("Rate limit or quota exceeded. Please try again later.") from e
        except APIConnectionError as e:
            raise ProviderConnectionError("Could not reach the provider. Check your network and try again.") from e

    async def _call(self, messages: list[dict], temperature: float, json_mode: bool) -> ChatResult:
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if self._extra_headers:
            kwargs["extra_headers"] = self._extra_headers
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        content = response.choices[0].message.content or ""
        return ChatResult(text=content, model=self._model)

    async def validate_key(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except AuthenticationError:
            return False
        except APIStatusError as e:
            # Some providers (notably OpenRouter, some custom gateways) don't
            # implement GET /models even with a valid key; fall back to a
            # minimal completion call to confirm the key itself works.
            if e.status_code in (401, 403):
                return False
            return await self._validate_via_minimal_completion()
        except Exception:
            return await self._validate_via_minimal_completion()

    async def _validate_via_minimal_completion(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return True
        except AuthenticationError:
            return False
        except Exception:
            # Ambiguous (e.g. bad model name, transient network issue) -
            # treat as "not confirmed connected" without crashing the UI.
            return False
