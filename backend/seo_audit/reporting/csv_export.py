"""CSV export of audit issues."""
from __future__ import annotations

import csv
import io

from ..db.models import Audit


def audit_to_csv(audit: Audit) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["severity", "code", "category", "url", "message", "impact", "recommendation", "example"]
    )
    for issue in audit.issues:
        writer.writerow(
            [
                issue.severity,
                issue.code,
                issue.category,
                issue.url or "",
                issue.message,
                issue.impact or "",
                issue.recommendation or "",
                issue.example or "",
            ]
        )
    return buf.getvalue().encode("utf-8")
