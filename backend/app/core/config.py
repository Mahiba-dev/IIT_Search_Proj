"""
Core configuration loaded from environment variables.
No secrets are hard-coded; the OpenAI API key is NEVER read from here —
it always comes from the per-request Authorization header sent by the
client, so it is never persisted server-side or logged.
"""
import os
from functools import lru_cache
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
    max_query_length: int = int(os.getenv("MAX_QUERY_LENGTH", "2000"))
    request_timeout_seconds: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
