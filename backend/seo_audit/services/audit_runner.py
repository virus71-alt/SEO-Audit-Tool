"""Orchestrate crawl → audits → scoring → persistence."""
from __future__ import annotations

import asyncio
import logging
import traceback
from datetime import datetime, timezone

from ..audits.base import BaseAudit, Issue
from ..audits.content import ContentAudit
from ..audits.images import ImageAudit
from ..audits.keywords import KeywordAudit
from ..audits.links import LinkAudit
from ..audits.mobile import MobileAudit
from ..audits.onpage import OnPageAudit
from ..audits.opengraph import OpenGraphAudit
from ..audits.performance import PerformanceAudit, fetch_psi
from ..audits.schema import SchemaAudit
from ..audits.technical import TechnicalAudit
from ..crawler import Crawler, CrawlResult
from ..db.base import SessionLocal
from ..db.models import Audit, Issue as IssueModel, Page as PageModel
from ..recommendations import RecommendationEngine
from ..scoring import Scorer

log = logging.getLogger(__name__)

AUDIT_PIPELINE: list[BaseAudit] = [
    TechnicalAudit(),
    OnPageAudit(),
    ContentAudit(),
    ImageAudit(),
    LinkAudit(),
    SchemaAudit(),
    OpenGraphAudit(),
    KeywordAudit(),
    MobileAudit(),
]


async def run_audit_async(
    audit_id: int,
    url: str,
    max_pages: int = 200,
    include_performance: bool = True,
) -> None:
    db = SessionLocal()
    audit = db.get(Audit, audit_id)
    if audit is None:
        log.error("audit %s not found", audit_id)
        db.close()
        return

    try:
        audit.status = "running"
        db.commit()

        crawler = Crawler(url, max_pages=max_pages)
        crawl: CrawlResult = await crawler.crawl()

        issues: list[Issue] = []
        for module in AUDIT_PIPELINE:
            try:
                issues.extend(module.run(crawl))
            except Exception as exc:
                log.exception("audit module %s failed: %s", module.name, exc)

        # Performance via PSI (homepage only; opt-in)
        if include_performance and crawl.pages:
            try:
                metrics = await fetch_psi(crawl.pages[0].final_url, strategy="mobile")
                perf = PerformanceAudit(metrics=[metrics])
                issues.extend(perf.run(crawl))
                if metrics.score is not None:
                    audit.performance_score = float(metrics.score)
            except Exception as exc:
                log.warning("performance audit failed: %s", exc)
                issues.extend(PerformanceAudit().run(crawl))

        # Enrich with recommendations
        engine = RecommendationEngine()
        issues = engine.enrich(issues)

        # Score
        score = Scorer().score(issues)

        audit.overall_score = score.overall
        audit.technical_score = score.technical
        audit.onpage_score = score.onpage
        audit.content_score = score.content
        audit.mobile_score = score.mobile
        if audit.performance_score is None:
            audit.performance_score = score.performance
        audit.pages_crawled = len(crawl.pages)
        audit.summary = {
            "issues_by_severity": score.issues_by_severity,
            "robots_loaded": crawl.robots_loaded,
            "sitemap_urls": len(crawl.sitemap_urls),
            "top_issues": [
                {"code": i.code, "severity": i.severity.value, "message": i.message}
                for i in engine.prioritized(issues, limit=10)
            ],
        }

        # Persist pages
        for page in crawl.pages:
            p = page.parsed
            db.add(
                PageModel(
                    audit_id=audit.id,
                    url=page.url,
                    status_code=page.status_code,
                    depth=page.depth,
                    title=p.title if p else None,
                    meta_description=p.meta_description if p else None,
                    canonical=p.canonical if p else None,
                    h1=p.h1 if p else None,
                    h2=p.h2 if p else None,
                    word_count=p.word_count if p else 0,
                    images=[{"src": i.src, "alt": i.alt} for i in p.images][:200] if p else None,
                    internal_links=[l.href for l in p.internal_links][:200] if p else None,
                    external_links=[l.href for l in p.external_links][:200] if p else None,
                    schema_blocks=p.schema_blocks if p else None,
                    open_graph=p.open_graph if p else None,
                    twitter=p.twitter if p else None,
                    response_time_ms=page.response_time_ms,
                )
            )

        # Persist issues
        for issue in issues:
            db.add(
                IssueModel(
                    audit_id=audit.id,
                    code=issue.code,
                    severity=issue.severity.value,
                    category=issue.category,
                    url=issue.url,
                    message=issue.message,
                    impact=issue.impact,
                    recommendation=issue.recommendation,
                    example=issue.example,
                    details=issue.details,
                )
            )

        audit.status = "done"
        audit.finished_at = datetime.now(timezone.utc)
        db.commit()

        # Notifications (best-effort)
        try:
            from .notification_service import notify_audit_complete

            notify_audit_complete(audit_id)
        except Exception:
            log.debug("notification skipped", exc_info=True)

    except Exception as exc:
        log.exception("audit failed: %s", exc)
        audit.status = "failed"
        audit.error = f"{exc}\n{traceback.format_exc()}"
        audit.finished_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


def run_audit_sync(audit_id: int, url: str, max_pages: int = 200, include_performance: bool = True) -> None:
    """Sync wrapper for BackgroundTasks / CLI."""
    asyncio.run(run_audit_async(audit_id, url, max_pages, include_performance))
