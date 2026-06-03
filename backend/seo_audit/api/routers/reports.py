"""Report download endpoints (HTML, PDF, CSV)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from ...db.base import get_db
from ...db.models import Audit, User
from ...reporting.csv_export import audit_to_csv
from ...reporting.html_report import render_html_report
from ...reporting.pdf_report import render_pdf_report
from ..deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


def _load(audit_id: int, user: User, db: Session) -> Audit:
    audit = db.get(Audit, audit_id)
    if not audit or audit.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Audit not found")
    return audit


@router.get("/{audit_id}/html", response_class=HTMLResponse)
def html(
    audit_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    audit = _load(audit_id, user, db)
    return HTMLResponse(render_html_report(audit))


@router.get("/{audit_id}/pdf")
def pdf(
    audit_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    audit = _load(audit_id, user, db)
    data = render_pdf_report(audit)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="audit-{audit.id}.pdf"'},
    )


@router.get("/{audit_id}/csv")
def csv(
    audit_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    audit = _load(audit_id, user, db)
    data = audit_to_csv(audit)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="audit-{audit.id}.csv"'},
    )
