"""Link analysis — internal/external broken/nofollow + link graph."""
from __future__ import annotations

from collections import Counter, defaultdict

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity


class LinkAudit(BaseAudit):
    name = "links"
    category = "links"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        status_by_url = {p.url.rstrip("/"): p.status_code for p in crawl.pages}

        inbound = Counter()
        outbound = defaultdict(list)
        for page in crawl.pages:
            if not page.parsed:
                continue
            for link in page.parsed.internal_links:
                target = link.href.rstrip("/")
                inbound[target] += 1
                outbound[page.url].append(target)
                if "nofollow" in (link.rel or []):
                    issues.append(
                        Issue(
                            code="internal_nofollow",
                            severity=Severity.LOW,
                            category=self.category,
                            message="Internal link uses rel=nofollow (passes no equity)",
                            url=page.url,
                            details={"target": target},
                        )
                    )
                code = status_by_url.get(target)
                if code and 300 <= code < 400:
                    issues.append(
                        Issue(
                            code="link_redirects",
                            severity=Severity.LOW,
                            category=self.category,
                            message=f"Internal link points to a redirect (HTTP {code})",
                            url=page.url,
                            details={"target": target, "status": code},
                        )
                    )

        # Orphan = page exists but no inbound internal link
        for page in crawl.pages:
            key = page.url.rstrip("/")
            if key not in inbound and page.depth > 0:
                issues.append(
                    Issue(
                        code="no_inbound_links",
                        severity=Severity.LOW,
                        category=self.category,
                        message="Page has no internal links pointing to it",
                        url=page.url,
                    )
                )

        return issues
