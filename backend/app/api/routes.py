from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.api.schemas import (
    ErrorResponse,
    KeyStatusRequest,
    KeyStatusResponse,
    ProviderModelInfo,
    ProvidersResponse,
    RejectedResponse,
    SearchRequest,
    SearchResponse,
)
from app.application.search_service import QueryRejected, SearchOrchestrationService
from app.application.validation_service import QueryValidationService
from app.core.config import get_settings
from app.core.security import get_provider_api_key, rate_limiter, redact_secrets
from app.domain.models import SearchQuery
from app.domain.providers import PROVIDER_REGISTRY
from app.infrastructure.providers.base import (
    InvalidApiKeyError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderUpstreamError,
    UnsupportedProviderConfigError,
)
from app.infrastructure.providers.factory import build_gateway

logger = logging.getLogger("ai_explorer.api")
router = APIRouter()


def _format_history(history: list[dict] | None, max_turns: int = 6) -> str:
    if not history:
        return ""
    trimmed = history[-max_turns:]
    lines = []
    for turn in trimmed:
        role = turn.get("role", "user")
        content = str(turn.get("content", ""))[:1000]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers():
    """Static catalog the frontend uses to populate the provider/model dropdowns."""
    return ProvidersResponse(
        providers=[
            ProviderModelInfo(
                id=meta.id.value,
                label=meta.label,
                default_model=meta.default_model,
                models=list(meta.models),
                default_base_url=meta.default_base_url,
                requires_base_url=meta.requires_base_url,
                supports_custom_model=meta.supports_custom_model,
                supports_temperature=meta.supports_temperature,
            )
            for meta in PROVIDER_REGISTRY.values()
        ]
    )


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={200: {"model": RejectedResponse}, 500: {"model": ErrorResponse}},
)
async def search(payload: SearchRequest, request: Request, api_key: str = Depends(get_provider_api_key)):
    settings = get_settings()
    client_key = payload.session_id or (request.client.host if request.client else "anonymous")
    rate_limiter.check(client_key)

    if len(payload.query) > settings.max_query_length:
        return JSONResponse(status_code=413, content=ErrorResponse(message="Query too long.").model_dump())

    try:
        gateway = build_gateway(
            provider=payload.provider,
            api_key=api_key,
            model=payload.model,
            base_url=payload.base_url,
            timeout=settings.request_timeout_seconds,
        )
    except UnsupportedProviderConfigError as e:
        return JSONResponse(status_code=400, content=ErrorResponse(message=str(e)).model_dump())

    validator = QueryValidationService(gateway)
    orchestrator = SearchOrchestrationService(gateway, validator)

    query = SearchQuery(
        text=payload.query.strip(),
        session_id=payload.session_id,
        provider=payload.provider,
        model=payload.model or PROVIDER_REGISTRY[payload.provider].default_model,
        temperature=payload.temperature,
    )
    history_context = _format_history(payload.history)

    try:
        answer = await orchestrator.search(query, history_context=history_context)
        return SearchResponse(
            query=answer.query,
            answer=answer.answer_markdown,
            summary=answer.summary,
            model=answer.model_used,
            provider=payload.provider.value,
            session_id=answer.session_id,
        )
    except QueryRejected as e:
        return JSONResponse(status_code=200, content=RejectedResponse(message=e.message).model_dump())
    except InvalidApiKeyError as e:
        return JSONResponse(status_code=401, content=ErrorResponse(message=str(e)).model_dump())
    except ProviderRateLimitError as e:
        return JSONResponse(status_code=429, content=ErrorResponse(message=str(e)).model_dump())
    except ProviderConnectionError as e:
        return JSONResponse(status_code=502, content=ErrorResponse(message=str(e)).model_dump())
    except ProviderUpstreamError as e:
        return JSONResponse(status_code=502, content=ErrorResponse(message=str(e)).model_dump())
    except Exception as e:  # noqa: BLE001 - last-resort safety net
        logger.error("Unhandled search error: %s", redact_secrets(str(e)))
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(message="An unexpected error occurred. Please try again.").model_dump(),
        )


@router.post("/key-status", response_model=KeyStatusResponse)
async def key_status(payload: KeyStatusRequest, api_key: str = Depends(get_provider_api_key)):
    try:
        gateway = build_gateway(
            provider=payload.provider,
            api_key=api_key,
            model=payload.model,
            base_url=payload.base_url,
        )
    except UnsupportedProviderConfigError:
        return KeyStatusResponse(connected=False, provider=payload.provider.value)

    try:
        ok = await gateway.validate_key()
        return KeyStatusResponse(
            connected=ok,
            provider=payload.provider.value,
            model=(payload.model or PROVIDER_REGISTRY[payload.provider].default_model) if ok else None,
        )
    except Exception as e:
        logger.warning("Key status check failed: %s", redact_secrets(str(e)))
        return KeyStatusResponse(connected=False, provider=payload.provider.value)


@router.get("/health")
async def health():
    return {"status": "ok"}
