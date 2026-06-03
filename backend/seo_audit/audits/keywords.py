"""Keyword and NLP entity extraction.

Uses NLTK if available; falls back to a pure-Python tokenizer so this module
works without a downloaded NLTK corpus or spaCy model.
"""
from __future__ import annotations

import logging
import re
from collections import Counter

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity

log = logging.getLogger(__name__)

STOPWORDS = {
    "the","a","an","and","or","of","to","in","for","on","with","is","are","was","were",
    "be","been","being","by","at","from","as","that","this","these","those","it","its",
    "but","not","no","so","if","than","then","do","does","did","you","your","we","our",
    "i","my","me","they","their","them","he","she","his","her","up","out","into","about",
    "over","under","more","most","some","any","each","every","will","would","can","could",
    "should","have","has","had","also","just","only","other","such","very","much","many",
}


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z][a-zA-Z'\-]{2,}", text)]


def _ngrams(tokens: list[str], n: int) -> list[str]:
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def extract_keywords(text: str, top_n: int = 25) -> dict:
    tokens = [t for t in _tokenize(text) if t not in STOPWORDS]
    total = len(tokens) or 1
    unigrams = Counter(tokens).most_common(top_n)
    bigrams = Counter(_ngrams(tokens, 2)).most_common(top_n)
    trigrams = Counter(_ngrams(tokens, 3)).most_common(top_n)
    return {
        "total_tokens": total,
        "top_unigrams": [{"term": w, "count": c, "density": c / total} for w, c in unigrams],
        "top_bigrams": [{"term": w, "count": c} for w, c in bigrams],
        "top_trigrams": [{"term": w, "count": c} for w, c in trigrams],
    }


class KeywordAudit(BaseAudit):
    name = "keywords"
    category = "content"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        for page in crawl.pages:
            if not page.parsed or not page.parsed.text:
                continue
            kw = extract_keywords(page.parsed.text, top_n=10)
            if not kw["top_unigrams"]:
                continue
            primary = kw["top_unigrams"][0]
            # Recommend if primary keyword is missing from title/H1
            title = (page.parsed.title or "").lower()
            h1 = " ".join(page.parsed.h1).lower()
            term = primary["term"]
            if term not in title and term not in h1 and primary["count"] >= 5:
                issues.append(
                    Issue(
                        code="keyword_not_in_title",
                        severity=Severity.LOW,
                        category=self.category,
                        message=(
                            f"Top body keyword {term!r} (used {primary['count']}×) "
                            "does not appear in title or H1"
                        ),
                        url=page.url,
                        details={"keyword": term, "density": primary["density"]},
                    )
                )
        return issues
