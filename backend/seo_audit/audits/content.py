"""Content quality audit — thin content, duplicates, keyword stuffing."""
from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity

THIN_CONTENT = 300
KEYWORD_STUFFING_DENSITY = 0.05  # 5%
STOPWORDS = {
    "the","a","an","and","or","of","to","in","for","on","with","is","are","was","were",
    "be","been","being","by","at","from","as","that","this","these","those","it","its",
    "but","not","no","so","if","than","then","do","does","did","you","your","we","our",
    "i","my","me","they","their","them","he","she","his","her","his","hers","up","out",
    "into","about","over","under","more","most","some","any","each","every",
}


def _content_fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").lower()).strip()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


class ContentAudit(BaseAudit):
    name = "content"
    category = "content"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        fingerprints: dict[str, list[str]] = defaultdict(list)

        for page in crawl.pages:
            p = page.parsed
            if not p:
                continue

            if p.word_count < THIN_CONTENT:
                issues.append(
                    Issue(
                        code="thin_content",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message=f"Thin content ({p.word_count} words; recommended ≥{THIN_CONTENT})",
                        url=page.url,
                    )
                )

            fingerprints[_content_fingerprint(p.text)].append(page.url)

            tokens = [t for t in re.findall(r"[a-zA-Z']{3,}", p.text.lower()) if t not in STOPWORDS]
            if tokens:
                top = Counter(tokens).most_common(1)[0]
                density = top[1] / len(tokens)
                if density > KEYWORD_STUFFING_DENSITY and top[1] > 10:
                    issues.append(
                        Issue(
                            code="keyword_stuffing",
                            severity=Severity.MEDIUM,
                            category=self.category,
                            message=f"Word {top[0]!r} occurs {top[1]} times ({density:.1%} density)",
                            url=page.url,
                            details={"token": top[0], "count": top[1], "density": density},
                        )
                    )

        for fp, urls in fingerprints.items():
            if len(urls) > 1:
                issues.append(
                    Issue(
                        code="duplicate_content",
                        severity=Severity.HIGH,
                        category=self.category,
                        message=f"{len(urls)} pages have identical body content",
                        details={"pages": urls[:10], "fingerprint": fp},
                    )
                )
        return issues
