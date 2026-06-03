"""Mobile SEO audit — viewport + responsive hints."""
from __future__ import annotations

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity


class MobileAudit(BaseAudit):
    name = "mobile"
    category = "mobile"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        for page in crawl.pages:
            p = page.parsed
            if not p:
                continue
            if not p.viewport:
                issues.append(
                    Issue(
                        code="missing_viewport",
                        severity=Severity.HIGH,
                        category=self.category,
                        message="Missing <meta name='viewport'> tag",
                        url=page.url,
                    )
                )
            elif "width=device-width" not in p.viewport.lower():
                issues.append(
                    Issue(
                        code="bad_viewport",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message=f"Viewport tag does not include width=device-width: {p.viewport!r}",
                        url=page.url,
                    )
                )
        return issues
