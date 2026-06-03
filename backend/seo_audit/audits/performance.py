"""Performance audit using Google PageSpeed Insights API.

If no API key is configured, falls back to local response-time heuristics.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from ..config import get_settings
from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity

log = logging.getLogger(__name__)

PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


@dataclass
class PerformanceMetrics:
    url: str
    score: float | None
    lcp_ms: float | None = None
    fcp_ms: float | None = None
    cls: float | None = None
    ttfb_ms: float | None = None
    tbt_ms: float | None = None
    raw: dict | None = None


async def fetch_psi(url: str, strategy: str = "mobile") -> PerformanceMetrics:
    settings = get_settings()
    if not settings.psi_api_key:
        return PerformanceMetrics(url=url, score=None)
    params = {"url": url, "key": settings.psi_api_key, "strategy": strategy, "category": "performance"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(PSI_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        log.warning("PSI fetch failed url=%s err=%s", url, exc)
        return PerformanceMetrics(url=url, score=None)

    lh = data.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    cats = lh.get("categories", {})

    def num(key: str) -> float | None:
        v = audits.get(key, {}).get("numericValue")
        return float(v) if v is not None else None

    return PerformanceMetrics(
        url=url,
        score=(cats.get("performance", {}).get("score") or 0) * 100 if cats else None,
        lcp_ms=num("largest-contentful-paint"),
        fcp_ms=num("first-contentful-paint"),
        cls=num("cumulative-layout-shift"),
        ttfb_ms=num("server-response-time"),
        tbt_ms=num("total-blocking-time"),
        raw=data,
    )


class PerformanceAudit(BaseAudit):
    name = "performance"
    category = "performance"

    def __init__(self, metrics: list[PerformanceMetrics] | None = None) -> None:
        self.metrics = metrics or []

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []

        # Local heuristic: very slow responses
        for page in crawl.pages:
            if page.response_time_ms and page.response_time_ms > 3000:
                issues.append(
                    Issue(
                        code="slow_response",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message=f"TTFB-like response time {page.response_time_ms} ms (>3s)",
                        url=page.url,
                    )
                )

        # PSI metrics if available
        for m in self.metrics:
            if m.lcp_ms and m.lcp_ms > 2500:
                issues.append(
                    Issue(
                        code="lcp_slow",
                        severity=Severity.HIGH if m.lcp_ms > 4000 else Severity.MEDIUM,
                        category=self.category,
                        message=f"LCP is {m.lcp_ms:.0f} ms (target <2500 ms)",
                        url=m.url,
                    )
                )
            if m.cls and m.cls > 0.1:
                issues.append(
                    Issue(
                        code="cls_high",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message=f"CLS is {m.cls:.3f} (target <0.1)",
                        url=m.url,
                    )
                )
            if m.fcp_ms and m.fcp_ms > 1800:
                issues.append(
                    Issue(
                        code="fcp_slow",
                        severity=Severity.LOW,
                        category=self.category,
                        message=f"FCP is {m.fcp_ms:.0f} ms (target <1800 ms)",
                        url=m.url,
                    )
                )
            if m.ttfb_ms and m.ttfb_ms > 800:
                issues.append(
                    Issue(
                        code="ttfb_slow",
                        severity=Severity.LOW,
                        category=self.category,
                        message=f"Server TTFB is {m.ttfb_ms:.0f} ms (target <800 ms)",
                        url=m.url,
                    )
                )
        return issues
