"""Celery application."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from ..config import get_settings

_settings = get_settings()

celery_app = Celery(
    "seo_audit",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=["seo_audit.tasks.audit_tasks", "seo_audit.tasks.notifications"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Recurring jobs: weekly Monday 06:00 UTC + monthly 1st 06:00 UTC.
celery_app.conf.beat_schedule = {
    "weekly-audits": {
        "task": "seo_audit.tasks.audit_tasks.run_scheduled_audits",
        "schedule": crontab(day_of_week="mon", hour=6, minute=0),
        "kwargs": {"cadence": "weekly"},
    },
    "monthly-audits": {
        "task": "seo_audit.tasks.audit_tasks.run_scheduled_audits",
        "schedule": crontab(day_of_month="1", hour=6, minute=0),
        "kwargs": {"cadence": "monthly"},
    },
}
