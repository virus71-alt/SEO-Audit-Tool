"""Typer CLI for headless audits."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .audits.content import ContentAudit
from .audits.images import ImageAudit
from .audits.keywords import KeywordAudit
from .audits.links import LinkAudit
from .audits.mobile import MobileAudit
from .audits.onpage import OnPageAudit
from .audits.opengraph import OpenGraphAudit
from .audits.performance import PerformanceAudit, fetch_psi
from .audits.schema import SchemaAudit
from .audits.technical import TechnicalAudit
from .crawler import Crawler
from .logging_setup import configure_logging
from .recommendations import RecommendationEngine
from .scoring import Scorer

app = typer.Typer(help="SEO Audit CLI")
console = Console()


@app.command()
def audit(
    url: str = typer.Argument(..., help="Website URL to audit"),
    max_pages: int = typer.Option(100, help="Maximum pages to crawl"),
    performance: bool = typer.Option(False, help="Run PageSpeed Insights (requires PSI_API_KEY)"),
    json_out: Path | None = typer.Option(None, "--json", help="Write full result to this JSON file"),
) -> None:
    """Run a full SEO audit against URL and print a summary."""
    configure_logging()
    asyncio.run(_run(url, max_pages, performance, json_out))


async def _run(url: str, max_pages: int, performance: bool, json_out: Path | None) -> None:
    console.print(f"[bold]Crawling[/bold] {url} (max {max_pages} pages)...")
    crawl = await Crawler(url, max_pages=max_pages).crawl()
    console.print(f"  -> {len(crawl.pages)} pages collected\n")

    modules = [
        TechnicalAudit(), OnPageAudit(), ContentAudit(), ImageAudit(),
        LinkAudit(), SchemaAudit(), OpenGraphAudit(), KeywordAudit(), MobileAudit(),
    ]
    issues = []
    for m in modules:
        try:
            issues.extend(m.run(crawl))
        except Exception as exc:
            console.print(f"[yellow]warn[/yellow] module {m.name} failed: {exc}")

    if performance and crawl.pages:
        metrics = await fetch_psi(crawl.pages[0].final_url)
        issues.extend(PerformanceAudit(metrics=[metrics]).run(crawl))

    issues = RecommendationEngine().enrich(issues)
    score = Scorer().score(issues)

    console.print(f"[bold green]Overall score:[/bold green] {score.overall}/100")
    table = Table(title="Category scores")
    table.add_column("Category"); table.add_column("Score", justify="right")
    for k, v in [("Technical", score.technical), ("On-Page", score.onpage),
                 ("Performance", score.performance), ("Content", score.content),
                 ("Mobile", score.mobile)]:
        table.add_row(k, f"{v}")
    console.print(table)

    sev_table = Table(title="Issues by severity")
    sev_table.add_column("Severity"); sev_table.add_column("Count", justify="right")
    for sev, count in score.issues_by_severity.items():
        sev_table.add_row(sev, str(count))
    console.print(sev_table)

    if json_out is None:
        from datetime import datetime
        result_dir = Path("Result")
        result_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        json_out = result_dir / f"{timestamp}.json"

    json_out.write_text(
        encoding="utf-8",
        data=json.dumps(
            {
                "url": url,
                "scores": score.__dict__,
                "issues": [
                    {
                        "code": i.code, "severity": i.severity.value, "category": i.category,
                        "url": i.url, "message": i.message, "impact": i.impact,
                        "recommendation": i.recommendation, "example": i.example,
                        "details": i.details,
                    }
                    for i in issues
                ],
            },
            indent=2, ensure_ascii=False,
        )
    )
    console.print(f"\n[green]OK[/green] wrote {json_out}")


if __name__ == "__main__":
    sys.exit(app())
