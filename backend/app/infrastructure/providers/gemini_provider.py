"""
Infrastructure: Google Gemini provider gateway.
"""
from __future__ import annotations

import re

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.infrastructure.providers.base import (
    ChatResult,
    InvalidApiKeyError,
    ProviderConnectionError,
    ProviderGateway,
    ProviderRateLimitError,
    ProviderUpstreamError,
)

_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class GeminiGateway(ProviderGateway):
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model_name = model
        genai.configure(api_key=api_key)

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

        model = genai.GenerativeModel(model_name=self._model_name, system_instruction=effective_system)
        try:
            response = await model.generate_content_async(
                user_message,
                generation_config=genai.GenerationConfig(temperature=temperature),
            )
            text = response.text or ""
            if json_mode:
                text = _CODE_FENCE.sub("", text).strip()
            return ChatResult(text=text, model=self._model_name)
        except google_exceptions.Unauthenticated as e:
            raise InvalidApiKeyError("The provided Gemini API key is invalid or unauthorized.") from e
        except google_exceptions.PermissionDenied as e:
            raise InvalidApiKeyError("The provided Gemini API key does not have access to this model.") from e
        except google_exceptions.ResourceExhausted as e:
            raise ProviderRateLimitError("Rate limit or quota exceeded. Please try again later.") from e
        except google_exceptions.ServiceUnavailable as e:
            raise ProviderConnectionError("Could not reach Gemini. Check your network and try again.") from e
        except google_exceptions.GoogleAPIError as e:
            raise ProviderUpstreamError(f"Gemini returned an error: {e}") from e

    async def validate_key(self) -> bool:
        try:
            model = genai.GenerativeModel(model_name=self._model_name)
            await model.generate_content_async("ping", generation_config=genai.GenerationConfig(max_output_tokens=1))
            return True
        except (google_exceptions.Unauthenticated, google_exceptions.PermissionDenied):
            return False
        except Exception:
            return False
