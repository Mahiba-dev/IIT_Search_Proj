"""
Domain layer: core entities and value objects for AI Explorer.
No dependency on FastAPI, OpenAI SDK, or any infrastructure concern.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from app.domain.providers import Provider


class QueryClassification(str, Enum):
    AI_RELATED = "ai_related"
    NOT_AI_RELATED = "not_ai_related"
    PARTIALLY_AI_RELATED = "partially_ai_related"


@dataclass(frozen=True)
class SearchQuery:
    """A single user search query within a session, targeting a specific
    provider/model chosen by the user in the sidebar."""
    text: str
    session_id: str
    provider: Provider
    model: str
    temperature: float = 0.3
    asked_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.text or not self.text.strip():
            raise ValueError("Query text must not be empty")


@dataclass(frozen=True)
class ValidationResult:
    classification: QueryClassification
    reason: str
    ai_related_excerpt: Optional[str] = None  # the AI-related portion, if partial

    @property
    def is_allowed(self) -> bool:
        return self.classification in (
            QueryClassification.AI_RELATED,
            QueryClassification.PARTIALLY_AI_RELATED,
        )


@dataclass(frozen=True)
class SearchAnswer:
    query: str
    answer_markdown: str
    summary: Optional[str]
    model_used: str
    session_id: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
