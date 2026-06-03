"""Audit endpoints — create, list, fetch detail."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.base import get_db
from ...db.models import Audit, User
from ...schemas.audit import AuditCreate, AuditDetail, AuditOut
from ..deps import get_current_user

router = APIRouter(prefix="/audits", tags=["audits"])


@router.post("", response_model=AuditOut, status_code=status.HTTP_202_ACCEPTED)
def create_audit(
    payload: AuditCreate,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Audit:
    audit = Audit(owner_id=user.id, url=str(payload.url), status="pending")
    db.add(audit)
    db.commit()
    db.refresh(audit)

    # Prefer Celery in production; fall back to BackgroundTasks for dev/test.
    try:
        from ...tasks.audit_tasks import run_audit_task

        run_audit_task.delay(
            audit.id,
            str(payload.url),
            payload.max_pages,
            payload.include_performance,
        )
    except Exception:
        from ...services.audit_runner import run_audit_sync

        background.add_task(
            run_audit_sync,
            audit.id,
            str(payload.url),
            payload.max_pages,
            payload.include_performance,
        )
    return audit


@router.get("", response_model=list[AuditOut])
def list_audits(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
) -> list[Audit]:
    stmt = (
        select(Audit)
        .where(Audit.owner_id == user.id)
        .order_by(Audit.started_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


@router.get("/{audit_id}", response_model=AuditDetail)
def get_audit(
    audit_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Audit:
    audit = db.get(Audit, audit_id)
    if not audit or audit.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Audit not found")
    return audit


@router.get("/{audit_id}/compare/{previous_id}")
def compare_audits(
    audit_id: int,
    previous_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    current = db.get(Audit, audit_id)
    previous = db.get(Audit, previous_id)
    if not current or not previous or current.owner_id != user.id or previous.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Audit(s) not found")

    def diff(a: float | None, b: float | None) -> float | None:
        if a is None or b is None:
            return None
        return round(a - b, 2)

    return {
        "current": current.id,
        "previous": previous.id,
        "overall_delta": diff(current.overall_score, previous.overall_score),
        "technical_delta": diff(current.technical_score, previous.technical_score),
        "onpage_delta": diff(current.onpage_score, previous.onpage_score),
        "performance_delta": diff(current.performance_score, previous.performance_score),
        "content_delta": diff(current.content_score, previous.content_score),
        "mobile_delta": diff(current.mobile_score, previous.mobile_score),
    }
