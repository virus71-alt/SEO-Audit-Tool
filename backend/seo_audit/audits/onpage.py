"""On-page SEO audit — titles, meta descriptions, heading structure."""
from __future__ import annotations

from collections import Counter

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity

TITLE_MIN = 50
TITLE_MAX = 60
META_MIN = 140
META_MAX = 160


class OnPageAudit(BaseAudit):
    name = "onpage"
    category = "onpage"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        titles = Counter()
        metas = Counter()

        for page in crawl.pages:
            p = page.parsed
            if not p:
                continue

            # Titles
            if not p.title:
                issues.append(
                    Issue(
                        code="missing_title",
                        severity=Severity.HIGH,
                        category=self.category,
                        message="Page has no <title> tag",
                        url=page.url,
                    )
                )
            else:
                titles[p.title] += 1
                length = len(p.title)
                if length < TITLE_MIN:
                    issues.append(
                        Issue(
                            code="title_too_short",
                            severity=Severity.LOW,
                            category=self.category,
                            message=f"Title too short ({length} chars; recommended {TITLE_MIN}-{TITLE_MAX})",
                            url=page.url,
                        )
                    )
                elif length > TITLE_MAX:
                    issues.append(
                        Issue(
                            code="title_too_long",
                            severity=Severity.LOW,
                            category=self.category,
                            message=f"Title too long ({length} chars; recommended {TITLE_MIN}-{TITLE_MAX})",
                            url=page.url,
                        )
                    )

            # Meta description
            if not p.meta_description:
                issues.append(
                    Issue(
                        code="missing_meta_description",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message="Page has no meta description",
                        url=page.url,
                    )
                )
            else:
                metas[p.meta_description] += 1
                length = len(p.meta_description)
                if length < META_MIN:
                    issues.append(
                        Issue(
                            code="meta_too_short",
                            severity=Severity.LOW,
                            category=self.category,
                            message=f"Meta description too short ({length} chars)",
                            url=page.url,
                        )
                    )
                elif length > META_MAX:
                    issues.append(
                        Issue(
                            code="meta_too_long",
                            severity=Severity.LOW,
                            category=self.category,
                            message=f"Meta description too long ({length} chars)",
                            url=page.url,
                        )
                    )

            # Headings
            if not p.h1:
                issues.append(
                    Issue(
                        code="missing_h1",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message="Page has no H1",
                        url=page.url,
                    )
                )
            elif len(p.h1) > 1:
                issues.append(
                    Issue(
                        code="multiple_h1",
                        severity=Severity.LOW,
                        category=self.category,
                        message=f"Page has {len(p.h1)} H1 tags",
                        url=page.url,
                    )
                )
            # Heading hierarchy: every heading level except the first should be at
            # most one greater than the prior level.
            previous = 0
            for level, _ in p.headings_order:
                if previous and level > previous + 1:
                    issues.append(
                        Issue(
                            code="heading_skip",
                            severity=Severity.LOW,
                            category=self.category,
                            message=f"Heading hierarchy skips levels (H{previous} → H{level})",
                            url=page.url,
                        )
                    )
                    break
                previous = level

        # Duplicates across the site
        for title, count in titles.items():
            if count > 1:
                issues.append(
                    Issue(
                        code="duplicate_title",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message=f"{count} pages share the title: {title!r}",
                        details={"count": count},
                    )
                )
        for meta, count in metas.items():
            if count > 1:
                issues.append(
                    Issue(
                        code="duplicate_meta",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message=f"{count} pages share the same meta description",
                        details={"count": count},
                    )
                )

        return issues
