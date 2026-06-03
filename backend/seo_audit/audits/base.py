"""Base classes for audit modules."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..crawler import CrawlResult


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Issue:
    code: str
    severity: Severity
    category: str
    message: str
    url: str | None = None
    impact: str | None = None
    recommendation: str | None = None
    example: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class BaseAudit(ABC):
    """Abstract audit; subclasses inspect a CrawlResult and emit issues."""

    name: str = "base"
    category: str = "general"

    @abstractmethod
    def run(self, crawl: CrawlResult) -> list[Issue]:
        ...
