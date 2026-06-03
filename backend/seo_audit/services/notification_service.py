"""Notification service — broken pages, score drops, SSL expiry, new issues."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from ..db.base import SessionLocal
from ..db.models import Audit, Issue
from .email_service import send_email

log = logging.getLogger(__name__)

SCORE_DROP_THRESHOLD = 10.0  # points


def notify_audit_complete(audit_id: int) -> None:
    db = SessionLocal()
    try:
        audit = db.get(Audit, audit_id)
        if not audit or not audit.owner:
            return

        previous = db.scalar(
            select(Audit)
            .where(
                Audit.url == audit.url,
                Audit.owner_id == audit.owner_id,
                Audit.id != audit.id,
                Audit.status == "done",
            )
            .order_by(Audit.started_at.desc())
            .limit(1)
        )

        broken_count = db.scalar(
            select(Issue)
            .where(Issue.audit_id == audit.id, Issue.code.in_(["status_404", "status_5xx", "broken_internal_link"]))
            .with_only_columns(Issue.id)
        )

        score_drop = None
        if previous and previous.overall_score and audit.overall_score:
            score_drop = previous.overall_score - audit.overall_score

        triggers: list[str] = []
        if broken_count:
            triggers.append(f"Broken pages found")
        if score_drop and score_drop >= SCORE_DROP_THRESHOLD:
            triggers.append(f"Score dropped {score_drop:.1f} points")

        if not triggers:
            return

        body = f"""<h3>SEO audit update for {audit.url}</h3>
<ul>{''.join(f'<li>{t}</li>' for t in triggers)}</ul>
<p>Overall score: <strong>{audit.overall_score}</strong>{f' (was {previous.overall_score})' if previous else ''}</p>
<p>Audit ID: {audit.id} · {datetime.now(timezone.utc).isoformat()}</p>
"""
        send_email(audit.owner.email, f"[SEO] Alert for {audit.url}", body)
    finally:
        db.close()


@__import__('functools').lru_cache(maxsize=128)
def _ssl_expiry_days(host: str) -> int | None:
    import socket
    import ssl
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter")
        if not not_after:
            return None
        expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        return (expires - datetime.now(timezone.utc)).days
    except Exception:
        return None


def check_ssl_expiry(host: str, alert_within_days: int = 14) -> int | None:
    days = _ssl_expiry_days(host)
    if days is not None and days <= alert_within_days:
        log.warning("SSL certificate for %s expires in %d days", host, days)
    return days
