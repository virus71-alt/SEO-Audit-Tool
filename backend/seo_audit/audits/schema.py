"""Structured data audit — JSON-LD schema presence and validation."""
from __future__ import annotations

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity

RECOMMENDED_TYPES = {
    "Article": ["headline", "author", "datePublished"],
    "BreadcrumbList": ["itemListElement"],
    "FAQPage": ["mainEntity"],
    "Organization": ["name"],
    "Product": ["name", "offers"],
}


def _flatten_types(block: dict | list) -> list[str]:
    out: list[str] = []
    if isinstance(block, list):
        for b in block:
            out.extend(_flatten_types(b))
        return out
    if not isinstance(block, dict):
        return out
    t = block.get("@type")
    if isinstance(t, str):
        out.append(t)
    elif isinstance(t, list):
        out.extend([x for x in t if isinstance(x, str)])
    if "@graph" in block:
        out.extend(_flatten_types(block["@graph"]))
    return out


def _iter_typed_objects(block):
    """Yield every dict in the JSON-LD that has an @type, walking @graph too."""
    if isinstance(block, list):
        for b in block:
            yield from _iter_typed_objects(b)
        return
    if not isinstance(block, dict):
        return
    if "@type" in block:
        yield block
    if "@graph" in block:
        yield from _iter_typed_objects(block["@graph"])


class SchemaAudit(BaseAudit):
    name = "schema"
    category = "schema"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        for page in crawl.pages:
            p = page.parsed
            if not p:
                continue
            if not p.schema_blocks:
                issues.append(
                    Issue(
                        code="missing_schema",
                        severity=Severity.LOW,
                        category=self.category,
                        message="Page has no JSON-LD structured data",
                        url=page.url,
                    )
                )
                continue
            for block in p.schema_blocks:
                typed_objs = list(_iter_typed_objects(block))
                if not typed_objs:
                    issues.append(
                        Issue(
                            code="schema_no_type",
                            severity=Severity.MEDIUM,
                            category=self.category,
                            message="JSON-LD block missing @type",
                            url=page.url,
                        )
                    )
                    continue
                for obj in typed_objs:
                    types = obj.get("@type")
                    type_list = [types] if isinstance(types, str) else list(types or [])
                    for t in type_list:
                        required = RECOMMENDED_TYPES.get(t)
                        if not required:
                            continue
                        missing = [f for f in required if f not in obj]
                        if missing:
                            issues.append(
                                Issue(
                                    code="schema_missing_fields",
                                    severity=Severity.LOW,
                                    category=self.category,
                                    message=f"Schema {t} missing required fields: {', '.join(missing)}",
                                    url=page.url,
                                    details={"type": t, "missing": missing},
                                )
                            )
        return issues
