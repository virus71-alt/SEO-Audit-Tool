"""Notification Celery tasks."""
from __future__ import annotations

from ..services.notification_service import check_ssl_expiry, notify_audit_complete
from .celery_app import celery_app


@celery_app.task(name="seo_audit.tasks.notifications.notify_audit_complete")
def notify_audit_complete_task(audit_id: int) -> None:
    notify_audit_complete(audit_id)


@celery_app.task(name="seo_audit.tasks.notifications.check_ssl")
def check_ssl_task(host: str) -> int | None:
    return check_ssl_expiry(host)
