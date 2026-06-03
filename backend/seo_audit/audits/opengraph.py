"""Open Graph & Twitter Card audit."""
from __future__ import annotations

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity

OG_REQUIRED = ["og:title", "og:description", "og:image", "og:url"]
TW_REQUIRED = ["twitter:card", "twitter:title", "twitter:description"]


class OpenGraphAudit(BaseAudit):
    name = "opengraph"
    category = "social"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        for page in crawl.pages:
            p = page.parsed
            if not p:
                continue
            missing_og = [k for k in OG_REQUIRED if k not in p.open_graph]
            if missing_og:
                issues.append(
                    Issue(
                        code="missing_og",
                        severity=Severity.LOW,
                        category=self.category,
                        message=f"Missing Open Graph tags: {', '.join(missing_og)}",
                        url=page.url,
                        details={"missing": missing_og},
                    )
                )
            missing_tw = [k for k in TW_REQUIRED if k not in p.twitter]
            if missing_tw and not p.twitter:
                issues.append(
                    Issue(
                        code="missing_twitter_card",
                        severity=Severity.LOW,
                        category=self.category,
                        message="No Twitter Card metadata",
                        url=page.url,
                    )
                )
        return issues
