# Architecture

Clean-architecture layering — domain entities, use-cases (services), adapters (crawler/HTTP/db), and delivery (FastAPI routers, CLI, Celery, frontend).

```
SEO/
├── README.md
├── ARCHITECTURE.md
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── backend/
│   └── seo_audit/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app factory
│       ├── cli.py                  # Typer CLI
│       ├── config.py               # Pydantic Settings
│       ├── logging_setup.py
│       ├── core/
│       │   ├── security.py         # JWT, password hashing
│       │   ├── exceptions.py
│       │   └── dependencies.py
│       ├── db/
│       │   ├── base.py             # SQLAlchemy Base, session
│       │   └── models.py           # User, Audit, Page, Issue, Score
│       ├── schemas/                # Pydantic DTOs
│       │   ├── audit.py
│       │   ├── user.py
│       │   └── report.py
│       ├── crawler/
│       │   ├── crawler.py          # async crawler core
│       │   ├── fetcher.py          # httpx wrapper
│       │   ├── robots.py
│       │   ├── sitemap.py
│       │   └── parser.py           # extract title/meta/headings/links/schema
│       ├── audits/
│       │   ├── base.py             # Audit interface, Issue, Severity
│       │   ├── technical.py        # status codes, redirects, indexability, https, depth
│       │   ├── onpage.py           # titles, meta, headings
│       │   ├── content.py          # thin content, duplicates, keyword stuffing
│       │   ├── images.py
│       │   ├── links.py            # broken / nofollow / orphan / graph
│       │   ├── schema.py           # JSON-LD / Schema.org
│       │   ├── opengraph.py        # OG + Twitter cards
│       │   ├── keywords.py         # NLTK / spaCy NLP
│       │   ├── mobile.py
│       │   └── performance.py      # PSI / Lighthouse integration
│       ├── scoring/
│       │   └── scorer.py           # weighted scoring
│       ├── recommendations/
│       │   ├── engine.py
│       │   └── library.py          # per-issue fix templates
│       ├── reporting/
│       │   ├── html_report.py      # Jinja2 dashboard
│       │   ├── pdf_report.py       # WeasyPrint
│       │   ├── csv_export.py
│       │   └── templates/
│       │       └── report.html
│       ├── api/
│       │   ├── deps.py
│       │   └── routers/
│       │       ├── auth.py
│       │       ├── audits.py
│       │       ├── reports.py
│       │       └── users.py
│       ├── tasks/
│       │   ├── celery_app.py
│       │   ├── audit_tasks.py
│       │   └── notifications.py
│       └── services/
│           ├── audit_runner.py     # orchestrates crawl → audits → score → store
│           ├── email_service.py
│           └── notification_service.py
├── frontend/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api.ts
│       ├── pages/
│       │   ├── Overview.tsx
│       │   ├── Technical.tsx
│       │   ├── Content.tsx
│       │   ├── Performance.tsx
│       │   ├── Links.tsx
│       │   ├── Images.tsx
│       │   ├── StructuredData.tsx
│       │   └── Recommendations.tsx
│       └── components/
│           ├── ScoreCard.tsx
│           ├── IssueTable.tsx
│           └── Charts.tsx
└── tests/
    ├── conftest.py
    ├── test_crawler.py
    ├── test_audits.py
    ├── test_scoring.py
    └── test_api.py
```

## Layering

1. **Domain** (`audits/`, `scoring/`, `recommendations/`) — pure logic, no I/O.
2. **Adapters** (`crawler/`, `db/`, `services/email_service.py`) — talk to the outside world.
3. **Use-cases** (`services/audit_runner.py`, `tasks/audit_tasks.py`) — orchestrate domain + adapters.
4. **Delivery** (`api/`, `cli.py`, `frontend/`) — turn HTTP/CLI into use-case calls.

## Audit pipeline

```
URL ──► Crawler ──► PageData[] ──► [Technical, OnPage, Content, Images,
                                    Links, Schema, OpenGraph, Keywords,
                                    Mobile, Performance] ──► Issue[]
                                            │
                                            ▼
                                  Scorer + Recommendations
                                            │
                                            ▼
                            DB persist → HTML / PDF / CSV report
```

## Extending

Add a new audit by subclassing `BaseAudit` (`audits/base.py`) and registering it in `services/audit_runner.AUDIT_PIPELINE`. Recommendations come from `recommendations/library.py` keyed by `Issue.code`.
