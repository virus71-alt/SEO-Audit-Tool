"""PDF report rendering via WeasyPrint (HTML → PDF)."""
from __future__ import annotations

from ..db.models import Audit
from .html_report import render_html_report


def render_pdf_report(audit: Audit) -> bytes:
    # Import inside function so the module is usable when WeasyPrint isn't installed.
    from weasyprint import HTML  # type: ignore

    html = render_html_report(audit)
    return HTML(string=html).write_pdf()
