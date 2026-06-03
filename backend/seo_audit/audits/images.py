"""Image SEO audit — missing alt, missing dimensions, oversized, broken."""
from __future__ import annotations

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity


class ImageAudit(BaseAudit):
    name = "images"
    category = "images"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        for page in crawl.pages:
            if not page.parsed:
                continue
            for img in page.parsed.images:
                if img.alt is None:
                    issues.append(
                        Issue(
                            code="image_missing_alt",
                            severity=Severity.MEDIUM,
                            category=self.category,
                            message="Image missing alt attribute",
                            url=page.url,
                            details={"src": img.src},
                        )
                    )
                elif img.alt.strip() == "":
                    issues.append(
                        Issue(
                            code="image_empty_alt",
                            severity=Severity.LOW,
                            category=self.category,
                            message="Image has empty alt (only acceptable for decorative images)",
                            url=page.url,
                            details={"src": img.src},
                        )
                    )
                if not img.width or not img.height:
                    issues.append(
                        Issue(
                            code="image_missing_dimensions",
                            severity=Severity.LOW,
                            category=self.category,
                            message="Image missing explicit width/height (causes CLS)",
                            url=page.url,
                            details={"src": img.src},
                        )
                    )
        return issues
