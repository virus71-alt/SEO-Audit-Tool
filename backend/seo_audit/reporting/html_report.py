"""Render the HTML audit report using Jinja2."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..db.models import Audit

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_html_report(audit: Audit) -> str:
    severity_counts: Counter = Counter()
    for issue in audit.issues:
        severity_counts[issue.severity] += 1

    severity_order = ["critical", "high", "medium", "low", "info"]
    ordered = {s: severity_counts.get(s, 0) for s in severity_order}

    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    issues_sorted = sorted(audit.issues, key=lambda i: rank.get(i.severity, 5))
    top_issues = issues_sorted[:15]

    template = _env.get_template("report.html")
    return template.render(
        audit=audit,
        issues=issues_sorted,
        top_issues=top_issues,
        severity_counts=ordered,
    )
