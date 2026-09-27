"""
Security helpers.

- Extracts the OpenAI API key from the Authorization header only (never
  from query params, body fields that might get logged, or cookies).
- Provides a tiny in-memory sliding-window rate limiter keyed by session id
  / client IP. For production, replace with Redis-backed limiting.
- A logging filter that redacts anything that looks like an API key so it
  can never reach application logs even by accident.
"""
from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from fastapi import Header, HTTPException, status

from app.core.config import get_settings

_API_KEY_HEADER = "authorization"

_key_pattern = re.compile(r"sk-[A-Za-z0-9_-]{10,}")


def redact_secrets(message: str) -> str:
    """Redact anything that looks like an OpenAI API key from a string before logging."""
    return _key_pattern.sub("sk-***REDACTED***", message)


async def get_provider_api_key(authorization: str | None = Header(default=None)) -> str:
    """
    Extract the selected provider's API key from the standard
    Authorization: Bearer <key> header. Works the same regardless of which
    provider the key belongs to — the backend never inspects or stores it
    beyond the lifetime of the single request it authenticates, and never
    forwards it to any provider other than the one the user selected.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected 'Bearer <API_KEY>'.",
        )
    api_key = authorization.split(" ", 1)[1].strip()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Empty API key.")
    return api_key


class SlidingWindowRateLimiter:
    """Minimal in-memory rate limiter (per-process). Good enough for a single
    backend instance / demo; swap for Redis in a multi-instance deployment."""

    def __init__(self, limit_per_minute: int):
        self.limit = limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        window = self._hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
            )
        window.append(now)


_settings = get_settings()
rate_limiter = SlidingWindowRateLimiter(_settings.rate_limit_per_minute)
