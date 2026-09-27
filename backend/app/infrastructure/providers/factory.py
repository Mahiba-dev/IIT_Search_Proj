"""
Infrastructure: factory that builds the right ProviderGateway for the
provider the user selected in the sidebar. This is the one place that
knows about every concrete provider implementation; everything else in
the app talks only to the ProviderGateway interface.
"""
from __future__ import annotations

from app.domain.providers import Provider, get_provider_metadata
from app.infrastructure.providers.anthropic_provider import AnthropicGateway
from app.infrastructure.providers.base import ProviderGateway, UnsupportedProviderConfigError
from app.infrastructure.providers.gemini_provider import GeminiGateway
from app.infrastructure.providers.openai_compatible import OpenAICompatibleGateway


def build_gateway(
    provider: Provider,
    api_key: str,
    model: str | None,
    base_url: str | None,
    timeout: float = 30.0,
) -> ProviderGateway:
    metadata = get_provider_metadata(provider)
    effective_model = model or metadata.default_model
    effective_base_url = base_url or metadata.default_base_url

    if metadata.requires_base_url and not effective_base_url:
        raise UnsupportedProviderConfigError(
            "This provider requires an API base URL. Please set it in the sidebar."
        )
    if not effective_model:
        raise UnsupportedProviderConfigError(
            "Please choose or enter a model for this provider."
        )

    if provider == Provider.ANTHROPIC:
        return AnthropicGateway(api_key=api_key, model=effective_model, timeout=timeout)

    if provider == Provider.GEMINI:
        return GeminiGateway(api_key=api_key, model=effective_model)

    # OpenAI, Mistral, Groq, DeepSeek, OpenRouter, Custom: all OpenAI-compatible.
    extra_headers = None
    if provider == Provider.OPENROUTER:
        extra_headers = {
            "HTTP-Referer": "https://ai-explorer.local",
            "X-Title": "AI Explorer",
        }

    return OpenAICompatibleGateway(
        api_key=api_key,
        model=effective_model,
        base_url=effective_base_url,
        timeout=timeout,
        extra_headers=extra_headers,
    )
