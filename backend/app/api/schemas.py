from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.domain.providers import Provider


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=128)
    provider: Provider
    model: Optional[str] = None
    base_url: Optional[str] = Field(default=None, max_length=500)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    # Short-form conversation history for follow-up questions:
    # list of {"role": "user"|"assistant", "content": str}, capped server-side.
    history: Optional[list[dict]] = None


class SearchResponse(BaseModel):
    status: Literal["ok"] = "ok"
    query: str
    answer: str
    summary: Optional[str] = None
    model: str
    provider: str
    session_id: str


class RejectedResponse(BaseModel):
    status: Literal["rejected"] = "rejected"
    message: str


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str


class KeyStatusRequest(BaseModel):
    provider: Provider
    model: Optional[str] = None
    base_url: Optional[str] = Field(default=None, max_length=500)


class KeyStatusResponse(BaseModel):
    connected: bool
    provider: str
    model: Optional[str] = None


class ProviderModelInfo(BaseModel):
    id: str
    label: str
    default_model: str
    models: list[str]
    default_base_url: Optional[str] = None
    requires_base_url: bool
    supports_custom_model: bool
    supports_temperature: bool


class ProvidersResponse(BaseModel):
    providers: list[ProviderModelInfo]
