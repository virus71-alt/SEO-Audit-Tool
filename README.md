# 🚀 SEO Audit Tool

A production-quality, modular SEO audit platform written in **Python 3.11+** with a **React** frontend.
Performs comprehensive technical, on-page, content, performance, mobile, structured-data, link, and keyword analysis — comparable in scope to Ahrefs Site Audit, SEMrush, Screaming Frog, and Google Search Console.

> **💡 Windows users:** All commands below use **PowerShell**. Python 3.11 is all you need for the CLI — no Docker required.

---

## ✨ Features at a glance

| Category | What it checks |
|---|---|
| **🛠️ Technical SEO** | 404/5xx pages, redirect chains & loops, soft 404s, noindex tags, canonical mismatches, HTTPS, mixed content, crawl depth, orphan pages, broken internal links |
| **📝 On-Page SEO** | Title length & duplicates, meta description length & duplicates, missing/multiple H1s, heading hierarchy skips |
| **✍️ Content** | Thin content (<300 words), duplicate body fingerprints, keyword stuffing, primary keyword missing from title/H1 |
| **🖼️ Images** | Missing alt text, empty alt, missing width/height (causes CLS) |
| **🔗 Links** | Broken internal links, redirecting links, nofollow abuse, pages with no inbound links |
| **🏷️ Structured Data** | JSON-LD presence, @type validation, required field checks (FAQPage, Article, Product, BreadcrumbList…) |
| **📱 Social** | Open Graph og:title/description/image/url, Twitter Cards |
| **📲 Mobile** | Missing or malformed viewport meta tag |
| **⚡ Performance** | Slow TTFB, LCP > 2.5s, CLS > 0.1, FCP > 1.8s via Google PageSpeed Insights API |

**🔢 Scoring** — weighted overall score out of 100:

```
Overall = Technical×30% + On-Page×25% + Performance×20% + Content×15% + Mobile×10%
```

**🤖 AI recommendations** — every issue ships with severity, SEO impact explanation, fix recommendation, and a code snippet.

**📊 Reports** — HTML dashboard · PDF export · CSV · JSON (CLI).

---

## 📁 Project structure

```
SEO/
├── backend/
│   └── seo_audit/
│       ├── main.py              # FastAPI app factory
│       ├── cli.py               # Typer CLI (runs without a database)
│       ├── config.py            # Settings loaded from .env
│       ├── crawler/             # Async BFS crawler, robots.txt, sitemap, HTML parser
│       ├── audits/              # 10 audit modules — one file each, all extend BaseAudit
│       ├── scoring/             # Weighted SEO scorer
│       ├── recommendations/     # Per-issue fix library (40+ templates)
│       ├── reporting/           # HTML / PDF / CSV generators + Jinja2 template
│       ├── api/                 # FastAPI routers (auth, audits, reports, users)
│       ├── tasks/               # Celery tasks + beat schedules
│       ├── services/            # Audit orchestrator, SMTP email, notifications
│       └── db/                  # SQLAlchemy models + session
├── frontend/                    # React 18 + Vite + Tailwind CSS dashboard
├── tests/                       # pytest suite (parser, audits, scorer, security…)
├── alembic/                     # Database migrations
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example                 # Copy to .env and fill in your values
```

---

## 💻 Option A — CLI only (Windows, no Docker needed)

Fastest way to run an audit. Only Python is required.

### 1. 📂 Open PowerShell and go to the project folder

```powershell
cd "C:\Users\YourName\Downloads\SEO"
```

### 2. 🐍 Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> **⚠️ "running scripts is disabled" error?** Run this once (no admin needed):
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> Then activate again.

### 3. 📦 Install the CLI dependencies

```powershell
pip install httpx beautifulsoup4 lxml protego tldextract typer rich "pydantic>=2.7" "pydantic-settings>=2.3" jinja2 tenacity
```

### 4. ⚡ Run an audit

```powershell
$env:PYTHONPATH = "$pwd\backend"
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m seo_audit.cli https://your-website.com --max-pages 50
```

You will see a live score table in the terminal and a timestamped report inside the `Result` folder (e.g. `Result/2026-06-09_19-17-50.json`).

### ⚙️ CLI options

| Flag | Default | What it does |
|---|---|---|
| `--max-pages N` | 100 | How many pages to crawl — increase for bigger sites |
| `--performance` | off | Call Google PageSpeed Insights (needs `PSI_API_KEY` in `.env`) |
| `--json PATH` | *(auto)* | Custom path to save the JSON file (defaults to `Result/` with current timestamp) |

### 🔍 Example — view your results

```powershell
$j = Get-Content Result\2026-06-09_19-17-50.json | ConvertFrom-Json
"Overall score: $($j.scores.overall)/100"
$j.issues | Format-Table severity, code, message -AutoSize
```

### 🚨 Example — CI score gate (fail build if score < 80)

```powershell
$env:PYTHONPATH = "$pwd\backend"
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m seo_audit.cli https://staging.example.com --max-pages 100 --json audit.json
$score = (Get-Content audit.json | ConvertFrom-Json).scores.overall
if ($score -lt 80) { Write-Error "SEO score $score is below threshold 80"; exit 1 }
```

---

## 🐳 Option B — Full stack (Web dashboard + PostgreSQL + Celery)

Use this when you want the web UI, user accounts, scheduled audits, email alerts, and downloadable PDF/HTML reports.

**Requires:** [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) with the WSL 2 backend enabled (reboot after install).

### 1. 📄 Copy the env file and set a secret key

```powershell
Copy-Item .env.example .env
```

Open `.env` in Notepad / VS Code and change `JWT_SECRET` to a long random string.
Generate one in PowerShell:

```powershell
[Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Maximum 256 }))
```

Paste the output as the `JWT_SECRET` value.

### 2. 🚀 Start all services

```powershell
docker compose up --build
```

First build takes 3–5 minutes. After that:

| Service | URL |
|---|---|
| **🔌 API + Swagger docs** | http://localhost:8000/docs |
| **🖥️ React dashboard** | http://localhost:3000 |
| **🩺 Health check** | http://localhost:8000/health |

### 3. 🔐 Register and run your first audit

**Via the dashboard:**
1. Open http://localhost:3000
2. Login → Register → create an account
3. Paste your URL on the Overview page → **Run audit**
4. Scores and charts appear in 30 s – 2 min

**Via PowerShell (REST API):**

```powershell
$BASE = "http://localhost:8000/api"

# Register
$body = @{ email = "me@example.com"; password = "hunter2hunter2" } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE/auth/register" -Method POST -ContentType "application/json" -Body $body

# Login — save the token
$form = "username=me@example.com&password=hunter2hunter2"
$token = (Invoke-RestMethod -Uri "$BASE/auth/login" -Method POST `
    -ContentType "application/x-www-form-urlencoded" -Body $form).access_token
$headers = @{ Authorization = "Bearer $token" }

# Start an audit
$auditBody = @{ url = "https://your-site.com"; max_pages = 100; include_performance = $false } | ConvertTo-Json
$audit = Invoke-RestMethod -Uri "$BASE/audits" -Method POST `
    -Headers $headers -ContentType "application/json" -Body $auditBody
$id = $audit.id

# Poll until done
do {
    Start-Sleep 5
    $a = Invoke-RestMethod -Uri "$BASE/audits/$id" -Headers $headers
    Write-Host "[$($a.status)] overall=$($a.overall_score)"
} while ($a.status -notin @("done","failed"))

# Download reports
Invoke-WebRequest "http://localhost:8000/api/reports/$id/html" -Headers $headers -OutFile "report.html"
Invoke-WebRequest "http://localhost:8000/api/reports/$id/csv"  -Headers $headers -OutFile "issues.csv"
Start-Process "report.html"   # opens in your default browser
```

### 🐳 Useful Docker commands

```powershell
docker compose up -d --build              # start everything in the background
docker compose logs -f api                # stream API logs
docker compose logs -f worker             # stream Celery worker logs
docker compose ps                         # see which services are running
docker compose down                       # stop (keeps the database volume)
docker compose down -v                    # stop and delete the database
docker compose exec api bash              # shell inside the API container
docker compose exec api pytest            # run the test suite inside Docker
docker compose exec api alembic upgrade head   # apply DB migrations
```

---

## ⚙️ Configuration reference (`.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | Postgres on `db` container | SQLAlchemy connection string |
| `REDIS_URL` | Redis on `redis` container | Redis URL for caching |
| `CELERY_BROKER_URL` | Redis on `redis` container | Celery task broker |
| `JWT_SECRET` | **change this!** | Signs auth tokens — must be long and random |
| `JWT_EXPIRE_MINUTES` | `1440` | Token lifetime (24 h) |
| `USER_AGENT` | `SEOAuditBot/1.0` | HTTP User-Agent sent during crawl |
| `MAX_PAGES_DEFAULT` | `500` | Default page cap per audit |
| `MAX_CONCURRENCY` | `10` | Concurrent HTTP requests during crawl |
| `REQUEST_TIMEOUT` | `20` | Per-request timeout in seconds |
| `PSI_API_KEY` | *(empty)* | [Google PageSpeed Insights API key](https://developers.google.com/speed/docs/insights/v5/get-started) — leave blank to skip |
| `SMTP_HOST` | *(empty)* | SMTP host for email alerts — leave blank to disable |
| `SMTP_USER` / `SMTP_PASSWORD` | — | SMTP credentials. For Gmail use an [App Password](https://myaccount.google.com/apppasswords) |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

---

## ⏰ Scheduled audits

The Celery beat service runs automatically in Docker:

| Schedule | When | What it does |
|---|---|---|
| Weekly | Every Monday 06:00 UTC | Re-audits every URL on file |
| Monthly | 1st of every month 06:00 UTC | Same |

To add a custom schedule, edit `backend\seo_audit\tasks\celery_app.py`:

```python
from celery.schedules import crontab
celery_app.conf.beat_schedule["nightly"] = {
    "task": "seo_audit.tasks.audit_tasks.run_scheduled_audits",
    "schedule": crontab(hour=2, minute=0),   # every night at 02:00 UTC
}
```

---

## 🧪 Running the tests

```powershell
# With the venv active (Option A)
$env:PYTHONPATH = "$pwd\backend"
.\.venv\Scripts\python.exe -m pytest tests\ -v

# Or inside Docker (Option B)
docker compose exec api pytest tests/ -v
```

Tests use in-memory SQLite — no external services required. Covers the HTML parser, all 10 audit modules, the scorer math, recommendation enrichment, keyword extraction, and JWT / password hashing.

---

## ➕ Adding a new audit module

**1.** Create `backend\seo_audit\audits\my_check.py`:

```python
from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity

class MyCheck(BaseAudit):
    name = "my_check"
    category = "technical"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues = []
        for page in crawl.pages:
            if page.parsed and "?utm_" in page.url:
                issues.append(Issue(
                    code="utm_in_canonical",
                    severity=Severity.LOW,
                    category=self.category,
                    message="UTM parameter found in canonical URL",
                    url=page.url,
                ))
        return issues
```

**2.** Register it in `backend\seo_audit\services\audit_runner.py`:

```python
from ..audits.my_check import MyCheck
AUDIT_PIPELINE.append(MyCheck())
```

**3.** Add a fix template in `backend\seo_audit\recommendations\library.py`:

```python
"utm_in_canonical": {
    "impact": "UTM parameters create duplicate pages that split ranking signals.",
    "recommendation": "Strip UTM params from canonical URLs; use server-side analytics instead.",
    "example": "<link rel='canonical' href='https://example.com/page'>",
},
```

That's it — the new check runs on every future audit automatically and its findings appear in all report formats.

---

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Crawler | httpx (async), BeautifulSoup4, lxml, Protego (robots.txt) |
| Database | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Task queue | Celery 5, Redis 7 |
| NLP / keywords | Regex tokenizer (works on Python 3.11, no spaCy model download needed) |
| Reporting | Jinja2 (HTML), WeasyPrint (PDF), Python csv |
| Frontend | React 18, Vite, Tailwind CSS, Recharts |
| Auth | JWT via python-jose, bcrypt via passlib |
| Deployment | Docker, Docker Compose |

---

## 🔍 Troubleshooting (Windows)

| Problem | Fix |
|---|---|
| `Activate.ps1 cannot be loaded — running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `'python' is not recognized as a command` | Reinstall Python 3.11 and tick **"Add python.exe to PATH"** during setup |
| `UnicodeEncodeError` in the terminal | Add `$env:PYTHONIOENCODING = "utf-8"` before running any command |
| Docker: `open //./pipe/dockerDesktopLinuxEngine` | Docker Desktop isn't fully started — click the whale icon in the system tray and wait for green |
| Port 8000 or 3000 already in use | `Get-NetTCPConnection -LocalPort 8000` → find the PID → `Stop-Process -Id <PID>` |
| Celery worker exits immediately | Windows doesn't support the default prefork pool — add `--pool=solo` to the worker command |
| PDF export fails outside Docker | Install the [GTK3 Runtime for Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) and restart PowerShell |
| `psycopg install error` — tries to compile | You need MSVC Build Tools, or just use Docker where it builds cleanly |

---

## 📄 License

MIT — free to use, modify, and distribute.
