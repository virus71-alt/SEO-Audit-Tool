"""Audit DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AuditCreate(BaseModel):
    url: HttpUrl
    max_pages: int = Field(default=200, ge=1, le=10000)
    include_performance: bool = True


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    severity: str
    category: str
    url: str | None = None
    message: str
    impact: str | None = None
    recommendation: str | None = None
    example: str | None = None
    details: dict[str, Any] | None = None


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    status_code: int | None
    depth: int
    title: str | None
    meta_description: str | None
    canonical: str | None
    h1: list | None
    h2: list | None
    word_count: int


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    pages_crawled: int
    overall_score: float | None
    technical_score: float | None
    onpage_score: float | None
    performance_score: float | None
    content_score: float | None
    mobile_score: float | None
    summary: dict | None
    error: str | None


class AuditDetail(AuditOut):
    issues: list[IssueOut] = []
    pages: list[PageOut] = []
