"""Celery tasks — async audits & scheduled re-audits."""
from __future__ import annotations

import logging

from sqlalchemy import select

from ..db.base import SessionLocal
from ..db.models import Audit
from ..services.audit_runner import run_audit_sync
from .celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name="seo_audit.tasks.audit_tasks.run_audit_task", bind=True, max_retries=2)
def run_audit_task(
    self,
    audit_id: int,
    url: str,
    max_pages: int = 200,
    include_performance: bool = True,
) -> dict:
    try:
        run_audit_sync(audit_id, url, max_pages, include_performance)
    except Exception as exc:
        log.exception("audit task failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
    return {"audit_id": audit_id, "status": "done"}


@celery_app.task(name="seo_audit.tasks.audit_tasks.run_scheduled_audits")
def run_scheduled_audits(cadence: str = "weekly") -> dict:
    """Re-run the latest audit per URL for every user."""
    db = SessionLocal()
    try:
        last = db.execute(
            select(Audit.owner_id, Audit.url).distinct()
        ).all()
        spawned = 0
        for owner_id, url in last:
            if not url:
                continue
            new = Audit(owner_id=owner_id, url=url, status="pending")
            db.add(new)
            db.commit()
            db.refresh(new)
            run_audit_task.delay(new.id, url, 200, True)
            spawned += 1
        return {"cadence": cadence, "spawned": spawned}
    finally:
        db.close()
