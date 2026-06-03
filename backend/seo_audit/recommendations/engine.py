"""Recommendation engine — enriches Issues with impact, fix, and example text."""
from __future__ import annotations

from ..audits.base import Issue
from . import library


class RecommendationEngine:
    """Adds impact / recommendation / example to issues using the library."""

    def enrich(self, issues: list[Issue]) -> list[Issue]:
        for issue in issues:
            rec = library.get(issue.code)
            if not rec:
                continue
            if not issue.impact:
                issue.impact = rec["impact"]
            if not issue.recommendation:
                issue.recommendation = rec["recommendation"]
            if not issue.example and rec["example"]:
                issue.example = rec["example"]
        return issues

    def prioritized(self, issues: list[Issue], limit: int = 25) -> list[Issue]:
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        return sorted(issues, key=lambda i: order.get(i.severity.value, 5))[:limit]
