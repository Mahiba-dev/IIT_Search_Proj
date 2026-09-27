"""
Application layer: orchestrates AI-only query validation.

Strategy (defense in depth, so prompt injection/rephrasing can't bypass it):
1. Fast keyword heuristic (domain layer) — if it clearly matches, short-circuit
   to AI_RELATED without spending an LLM call.
2. Otherwise, ask the LLM to classify the query using a locked-down system
   prompt that treats the query text as untrusted data, never as instructions.
3. The classification decision is made server-side and enforced independently
   of anything the frontend does.
"""
from __future__ import annotations

import json
import logging

from app.domain.ai_topic_rules import (
    AI_ONLY_SYSTEM_PROMPT,
    CLASSIFIER_SYSTEM_PROMPT,
    has_ai_keyword_signal,
)
from app.domain.models import QueryClassification, ValidationResult
from app.infrastructure.providers.base import ProviderGateway

logger = logging.getLogger("ai_explorer.validation")

REJECTION_MESSAGE = (
    "This search is limited to Artificial Intelligence topics. "
    "Please enter an AI-related question."
)


class QueryValidationService:
    """Validates queries against the AI-only restriction using whichever
    provider gateway the user has configured — the same provider they'll
    get their answer from, so no other provider's key is ever touched."""

    def __init__(self, gateway: ProviderGateway):
        self._gateway = gateway

    async def validate(self, query_text: str) -> ValidationResult:
        # Fast path: obvious AI keyword signal present.
        if has_ai_keyword_signal(query_text):
            return ValidationResult(
                classification=QueryClassification.AI_RELATED,
                reason="Matched known AI-domain terminology.",
            )

        # Slow path: LLM classification, with the query treated as data only.
        result = await self._gateway.chat(
            system_prompt=CLASSIFIER_SYSTEM_PROMPT,
            user_message=json.dumps({"query": query_text}),
            json_mode=True,
            temperature=0.0,
        )
        try:
            parsed = json.loads(result.text)
            classification = QueryClassification(parsed["classification"].lower())
            return ValidationResult(
                classification=classification,
                reason=parsed.get("reason", ""),
                ai_related_excerpt=parsed.get("ai_related_excerpt"),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Classifier returned unparseable output: %s", e)
            # Fail closed: if we can't confidently classify it, don't answer it.
            return ValidationResult(
                classification=QueryClassification.NOT_AI_RELATED,
                reason="Could not confidently classify the query as AI-related.",
            )
