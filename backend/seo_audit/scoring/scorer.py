"""Weighted SEO scoring.

Each category starts at 100. Issues subtract points by severity, capped so that
no single category drops below zero. The overall score is a weighted average.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..audits.base import Issue, Severity

SEVERITY_PENALTY = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 12,
    Severity.MEDIUM: 5,
    Severity.LOW: 2,
    Severity.INFO: 0,
}

CATEGORY_WEIGHTS = {
    "technical": 0.30,
    "onpage": 0.25,
    "performance": 0.20,
    "content": 0.15,
    "mobile": 0.10,
}

# Categories not directly weighted still count via the technical bucket.
CATEGORY_BUCKET = {
    "technical": "technical",
    "onpage": "onpage",
    "content": "content",
    "performance": "performance",
    "mobile": "mobile",
    "images": "onpage",
    "schema": "onpage",
    "social": "onpage",
    "links": "technical",
}


@dataclass
class ScoreBreakdown:
    overall: float
    technical: float
    onpage: float
    performance: float
    content: float
    mobile: float
    issues_by_severity: dict[str, int] = field(default_factory=dict)


class Scorer:
    def score(self, issues: list[Issue]) -> ScoreBreakdown:
        bucket_penalties: dict[str, float] = {k: 0.0 for k in CATEGORY_WEIGHTS}
        sev_counts: dict[str, int] = {s.value: 0 for s in Severity}

        for issue in issues:
            sev_counts[issue.severity.value] = sev_counts.get(issue.severity.value, 0) + 1
            bucket = CATEGORY_BUCKET.get(issue.category, "technical")
            bucket_penalties[bucket] += SEVERITY_PENALTY.get(issue.severity, 0)

        def clamp(v: float) -> float:
            return round(max(0.0, min(100.0, 100.0 - v)), 1)

        technical = clamp(bucket_penalties["technical"])
        onpage = clamp(bucket_penalties["onpage"])
        performance = clamp(bucket_penalties["performance"])
        content = clamp(bucket_penalties["content"])
        mobile = clamp(bucket_penalties["mobile"])

        overall = round(
            technical * CATEGORY_WEIGHTS["technical"]
            + onpage * CATEGORY_WEIGHTS["onpage"]
            + performance * CATEGORY_WEIGHTS["performance"]
            + content * CATEGORY_WEIGHTS["content"]
            + mobile * CATEGORY_WEIGHTS["mobile"],
            1,
        )

        return ScoreBreakdown(
            overall=overall,
            technical=technical,
            onpage=onpage,
            performance=performance,
            content=content,
            mobile=mobile,
            issues_by_severity=sev_counts,
        )
