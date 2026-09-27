import pytest
from unittest.mock import AsyncMock

from app.application.search_service import QueryRejected, SearchOrchestrationService
from app.domain.models import QueryClassification, SearchQuery, ValidationResult
from app.domain.providers import Provider
from app.infrastructure.providers.base import ChatResult


@pytest.mark.asyncio
async def test_search_returns_answer_for_ai_related_query():
    gateway = AsyncMock()
    gateway.chat = AsyncMock(return_value=ChatResult(text="Transformers use self-attention.", model="gpt-4.1"))

    validator = AsyncMock()
    validator.validate = AsyncMock(
        return_value=ValidationResult(classification=QueryClassification.AI_RELATED, reason="ok")
    )

    service = SearchOrchestrationService(gateway, validator)
    query = SearchQuery(text="How do transformers work?", session_id="s1", provider=Provider.OPENAI, model="gpt-4.1")

    answer = await service.search(query)

    assert "self-attention" in answer.answer_markdown
    assert answer.model_used == "gpt-4.1"
    assert answer.session_id == "s1"


@pytest.mark.asyncio
async def test_search_rejects_non_ai_query_without_calling_provider_for_answer():
    gateway = AsyncMock()
    gateway.chat = AsyncMock(return_value=ChatResult(text="should not be called", model="claude-sonnet-4-6"))

    validator = AsyncMock()
    validator.validate = AsyncMock(
        return_value=ValidationResult(classification=QueryClassification.NOT_AI_RELATED, reason="unrelated")
    )

    service = SearchOrchestrationService(gateway, validator)
    query = SearchQuery(
        text="What's the weather today?", session_id="s1", provider=Provider.ANTHROPIC, model="claude-sonnet-4-6"
    )

    with pytest.raises(QueryRejected):
        await service.search(query)

    gateway.chat.assert_not_called()


@pytest.mark.asyncio
async def test_partial_query_uses_isolated_ai_excerpt_only():
    gateway = AsyncMock()
    gateway.chat = AsyncMock(return_value=ChatResult(text="answer", model="gemini-2.5-flash"))

    validator = AsyncMock()
    validator.validate = AsyncMock(
        return_value=ValidationResult(
            classification=QueryClassification.PARTIALLY_AI_RELATED,
            reason="mixed",
            ai_related_excerpt="what is fine-tuning",
        )
    )

    service = SearchOrchestrationService(gateway, validator)
    query = SearchQuery(
        text="Plan my vacation and explain what is fine-tuning",
        session_id="s1",
        provider=Provider.GEMINI,
        model="gemini-2.5-flash",
    )

    await service.search(query)

    called_user_message = gateway.chat.call_args.kwargs["user_message"]
    assert "what is fine-tuning" in called_user_message
    assert "vacation" not in called_user_message


@pytest.mark.asyncio
async def test_temperature_is_forwarded_to_provider():
    gateway = AsyncMock()
    gateway.chat = AsyncMock(return_value=ChatResult(text="answer", model="gpt-4.1"))
    validator = AsyncMock()
    validator.validate = AsyncMock(
        return_value=ValidationResult(classification=QueryClassification.AI_RELATED, reason="ok")
    )

    service = SearchOrchestrationService(gateway, validator)
    query = SearchQuery(
        text="Explain embeddings", session_id="s1", provider=Provider.OPENAI, model="gpt-4.1", temperature=0.9
    )

    await service.search(query)

    assert gateway.chat.call_args.kwargs["temperature"] == 0.9


def test_search_query_rejects_empty_text():
    with pytest.raises(ValueError):
        SearchQuery(text="   ", session_id="s1", provider=Provider.OPENAI, model="gpt-4.1")
