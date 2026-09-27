"""
Application layer: orchestrates validation + answer generation.
"""
from __future__ import annotations

from app.domain.ai_topic_rules import AI_ONLY_SYSTEM_PROMPT
from app.domain.models import SearchAnswer, SearchQuery
from app.application.validation_service import REJECTION_MESSAGE, QueryValidationService
from app.infrastructure.providers.base import ProviderGateway


class QueryRejected(Exception):
    def __init__(self, message: str = REJECTION_MESSAGE):
        super().__init__(message)
        self.message = message


class SearchOrchestrationService:
    def __init__(self, gateway: ProviderGateway, validator: QueryValidationService):
        self._gateway = gateway
        self._validator = validator

    async def search(self, query: SearchQuery, history_context: str = "") -> SearchAnswer:
        validation = await self._validator.validate(query.text)

        if not validation.is_allowed:
            raise QueryRejected()

        # For partial matches, only answer the AI-related excerpt if the
        # classifier isolated one; otherwise fall back to the full query
        # (the answering system prompt itself will refuse non-AI parts).
        effective_query = validation.ai_related_excerpt or query.text

        user_message = effective_query
        if history_context:
            user_message = f"Conversation so far (for context):\n{history_context}\n\nNew question: {effective_query}"

        result = await self._gateway.chat(
            system_prompt=AI_ONLY_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=query.temperature,
        )

        summary = self._extract_summary(result.text)

        return SearchAnswer(
            query=query.text,
            answer_markdown=result.text,
            summary=summary,
            model_used=result.model,
            session_id=query.session_id,
        )

    @staticmethod
    def _extract_summary(answer_markdown: str) -> str | None:
        """Long answers get a short summary line for the UI to show up top."""
        if len(answer_markdown) < 400:
            return None
        first_paragraph = answer_markdown.strip().split("\n\n")[0]
        return first_paragraph[:220] + ("…" if len(first_paragraph) > 220 else "")
