"""Report DTOs."""
from __future__ import annotations

from pydantic import BaseModel


class ReportRequest(BaseModel):
    audit_id: int
    format: str = "html"  # html|pdf|csv
