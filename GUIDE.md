# SEO Audit Tool — User Guide (Windows)

A practical, end-to-end walkthrough for installing, running, and extending the platform on **Windows 10 / 11**. All commands use **PowerShell**.

> **TL;DR:** Install Docker Desktop, copy `.env.example` → `.env`, run `docker compose up --build`, open http://localhost:3000.

---

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration-env)
4. [Path A — Docker Desktop (recommended)](#4-path-a--docker-desktop-recommended)
5. [Path B — Native Windows (no Docker)](#5-path-b--native-windows-no-docker)
6. [First audit — three ways](#6-first-audit--three-ways)
7. [Understanding the report](#7-understanding-the-report)
8. [REST API reference](#8-rest-api-reference)
9. [CLI reference](#9-cli-reference)
10. [Scheduled & recurring audits](#10-scheduled--recurring-audits)
11. [Email notifications](#11-email-notifications)
12. [Database & migrations](#12-database--migrations)
13. [Extending the tool](#13-extending-the-tool)
14. [Testing](#14-testing)
15. [Troubleshooting (Windows-specific)](#15-troubleshooting-windows-specific)
16. [FAQ](#16-faq)

---

## 1. Prerequisites

### Strongly recommended (Path A — Docker)

| Component | Where to get it |
|---|---|
| **Docker Desktop for Windows** | https://www.docker.com/products/docker-desktop/ — enable the **WSL 2 backend** during install. |
| **Git for Windows** (optional) | https://git-scm.com/download/win |
| A modern terminal | Windows Terminal (Microsoft Store) — better than `cmd.exe`. |

That's it. Docker gives you Python, Postgres, Redis, Celery, and Node without installing any of them on Windows directly.

### Only needed for native (Path B)

| Component | Where to get it |
|---|---|
| **Python 3.12** | https://www.python.org/downloads/windows/ — tick **"Add python.exe to PATH"** during install. |
| **Node.js 20 LTS** | https://nodejs.org/ (Windows Installer .msi). |
| **PostgreSQL 16** | https://www.postgresql.org/download/windows/ |
| **Redis** | Windows isn't officially supported — use **Memurai** (https://www.memurai.com/) or run Redis in WSL2 / Docker. |
| **GTK libs for WeasyPrint (PDF export)** | https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases — install the all-in-one bundle. |
| **PageSpeed Insights API key** (optional) | https://developers.google.com/speed/docs/insights/v5/get-started |

> **Why Docker is easier:** Celery and Redis don't run cleanly on Windows. WeasyPrint needs native GTK libraries. Docker sidesteps all of this.

---

## 2. Installation

Open **PowerShell** in the folder where you want to put the project:

```powershell
cd $env:USERPROFILE\Downloads
# If you already extracted the project, just cd into it:
cd "$env:USERPROFILE\Downloads\SEO"

# Copy the env template (PowerShell syntax)
Copy-Item .env.example .env
```

Open `.env` in Notepad or VS Code:

```powershell
notepad .env
# or
code .env
```

At minimum, set a long random `JWT_SECRET`. A quick way to generate one in PowerShell:

```powershell
[Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## 3. Configuration (`.env`)

| Variable | What it does |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL. Default points at the bundled Postgres container. |
| `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis URIs. |
| `JWT_SECRET` | **Change this in production.** Signs auth tokens. |
| `JWT_EXPIRE_MINUTES` | Token lifetime (default 1440 = 24h). |
| `USER_AGENT` | Sent on every crawl request. Include a contact URL. |
| `MAX_PAGES_DEFAULT` | Default page cap. |
| `MAX_CONCURRENCY` | Concurrent HTTP requests during crawl. |
| `REQUEST_TIMEOUT` | Per-request timeout in seconds. |
| `PSI_API_KEY` | Google PageSpeed Insights key. Leave blank to disable PSI. |
| `SMTP_*` | SMTP settings for email notifications. Leave host blank to disable. |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

---

## 4. Path A — Docker Desktop (recommended)

### One-time setup

1. Install **Docker Desktop** and reboot.
2. Open Docker Desktop once and wait for the whale icon to turn green.
3. In **Settings → Resources → File Sharing**, make sure `C:\Users\<you>` is shared (it is by default).

### Start everything

```powershell
cd "$env:USERPROFILE\Downloads\SEO"
docker compose up --build
```

First build takes 3–5 minutes (downloading Python base image, installing GTK for WeasyPrint, etc.). Subsequent starts are seconds.

You should see six containers come up:

| Service | URL / port | Purpose |
|---|---|---|
| `api` | http://localhost:8000 | FastAPI backend. Swagger UI at `/docs`. |
| `frontend` | http://localhost:3000 | React dashboard. |
| `worker` | — | Celery worker that runs audits. |
| `beat` | — | Celery beat scheduler. |
| `db` | localhost:5432 | PostgreSQL 16. |
| `redis` | localhost:6379 | Redis 7. |

Verify the API is alive (in a **new** PowerShell window):

```powershell
Invoke-RestMethod http://localhost:8000/health
# StatusCode: 200, body: { status = "ok" }
```

### Useful Docker commands (PowerShell)

```powershell
# Run in the background instead of attaching the terminal
docker compose up -d --build

# Tail logs for one service
docker compose logs -f api
docker compose logs -f worker

# See what's running
docker compose ps

# Stop everything (keeps the database)
docker compose down

# Stop and wipe the Postgres volume too
docker compose down -v

# Rebuild after editing dependencies
docker compose build --no-cache api

# Open a shell inside the API container
docker compose exec api bash
```

---

## 5. Path B — Native Windows (no Docker)

Use this only if Docker Desktop isn't an option. You'll need Postgres + Redis (or Memurai) installed and running first.

### Backend

```powershell
cd "$env:USERPROFILE\Downloads\SEO"

# Create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# If activation is blocked by execution policy, run once as admin:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Install dependencies
pip install -e ".[dev]"

# Point .env at your local Postgres / Redis (edit DATABASE_URL etc. accordingly)
# Then launch the API
$env:PYTHONPATH = "$pwd\backend"
uvicorn seo_audit.main:app --reload --app-dir backend
```

API is now at http://localhost:8000.

### Celery worker (separate PowerShell window)

Celery on Windows must use the **solo** pool:

```powershell
cd "$env:USERPROFILE\Downloads\SEO"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "$pwd\backend"

celery -A seo_audit.tasks.celery_app:celery_app worker --loglevel=INFO --pool=solo
```

### Celery beat (separate window, optional)

```powershell
celery -A seo_audit.tasks.celery_app:celery_app beat --loglevel=INFO
```

### Frontend (separate window)

```powershell
cd "$env:USERPROFILE\Downloads\SEO\frontend"
npm install
npm run dev
```

Frontend at http://localhost:3000. Note: the Vite proxy in [`vite.config.ts`](frontend/vite.config.ts) targets `http://api:8000` (the Docker hostname). For native dev, edit it to `http://localhost:8000`.

### WeasyPrint (PDF export) on native Windows

PDF reports require the GTK runtime. Install **GTK3 Runtime for Windows** from:
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

After installing, restart PowerShell so the new PATH is picked up. If PDFs still fail, you can skip them and use HTML/CSV exports.

---

## 6. First audit — three ways

### A. Web UI (easiest)

1. Open **http://localhost:3000** in your browser
2. Click **Login** → **Register** → create an account
3. Enter a URL on the Overview page (e.g. `https://example.com`) and click **Run audit**
4. Scores + charts appear in 30s – 2min depending on site size

### B. REST API from PowerShell

```powershell
$BASE = "http://localhost:8000/api"

# Register
$body = @{ email = "me@example.com"; password = "hunter2hunter2" } | ConvertTo-Json
Invoke-RestMethod -Uri "$BASE/auth/register" -Method POST -ContentType "application/json" -Body $body

# Log in (form-encoded, like OAuth2)
$form = "username=me@example.com&password=hunter2hunter2"
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method POST `
    -ContentType "application/x-www-form-urlencoded" -Body $form
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }

# Start an audit
$auditBody = @{ url = "https://example.com"; max_pages = 100; include_performance = $true } | ConvertTo-Json
$audit = Invoke-RestMethod -Uri "$BASE/audits" -Method POST -Headers $headers `
    -ContentType "application/json" -Body $auditBody
$id = $audit.id
"Audit #$id started"

# Poll until it's done
while ($true) {
    $a = Invoke-RestMethod -Uri "$BASE/audits/$id" -Headers $headers
    "[$($a.status)] score=$($a.overall_score)"
    if ($a.status -in @("done", "failed")) { break }
    Start-Sleep -Seconds 5
}

# Download reports to the current directory
Invoke-WebRequest -Uri "$BASE/../api/reports/$id/html" -Headers $headers -OutFile "report.html"
Invoke-WebRequest -Uri "$BASE/../api/reports/$id/pdf"  -Headers $headers -OutFile "report.pdf"
Invoke-WebRequest -Uri "$BASE/../api/reports/$id/csv"  -Headers $headers -OutFile "issues.csv"
Start-Process "report.html"   # open in default browser
```

### C. CLI (no backend / database needed)

The CLI runs the full audit in-process. Perfect for ad-hoc checks or CI.

```powershell
# Inside the activated venv (Path B)
seo-audit audit https://example.com --max-pages 100 --json result.json

# Or via Docker without ever leaving the API container
docker compose exec api seo-audit audit https://example.com --max-pages 100 --json /tmp/result.json
docker compose cp api:/tmp/result.json .\result.json
```

---

## 7. Understanding the report

### Scores

Every category starts at **100** and loses points per issue:

| Severity | Points off |
|---|---|
| Critical | 25 |
| High | 12 |
| Medium | 5 |
| Low | 2 |
| Info | 0 |

The **Overall** score is a weighted average:

```
Overall = Technical×0.30 + OnPage×0.25 + Performance×0.20 + Content×0.15 + Mobile×0.10
```

### Issue anatomy

| Field | Example |
|---|---|
| `code` | `missing_title` |
| `severity` | `critical` / `high` / `medium` / `low` / `info` |
| `category` | `technical`, `onpage`, `content`, `images`, `links`, `schema`, `social`, `mobile`, `performance` |
| `url` | The affected page (or `null` for site-wide) |
| `message` | What was detected |
| `impact` | Why it matters for SEO |
| `recommendation` | How to fix it |
| `example` | Code or config snippet |
| `details` | Extra structured data |

### Categories at a glance

- **Technical** — 404/5xx, redirect chains/loops, soft 404s, noindex, canonical mismatches, HTTPS, mixed content, deep pages, orphan pages, broken internal links.
- **On-Page** — title/meta length+duplicates+missing, H1 missing/multiple, heading hierarchy skips.
- **Content** — thin (<300 words), duplicate body fingerprints, keyword stuffing, primary keyword missing from title/H1.
- **Images** — missing `alt`, empty `alt`, missing `width`/`height`.
- **Links** — broken internal, redirecting internal, internal `rel=nofollow`, no inbound links.
- **Schema** — no JSON-LD, missing `@type`, missing required schema.org fields.
- **Social** — missing OG / Twitter Cards.
- **Mobile** — missing or bad viewport.
- **Performance** — slow TTFB, LCP > 2.5s, CLS > 0.1, FCP > 1.8s (via PSI when key is set).

---

## 8. REST API reference

Swagger UI: **http://localhost:8000/docs** · ReDoc: **/redoc**

### Auth

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/auth/register` | `{email, password}` | User |
| POST | `/api/auth/login` | form `username=email&password=…` | `{access_token, token_type}` |

Send the token on every other call: `Authorization: Bearer <token>`.

### Audits

| Method | Path | Notes |
|---|---|---|
| POST | `/api/audits` | `{url, max_pages, include_performance}` — returns immediately |
| GET | `/api/audits` | List your audits |
| GET | `/api/audits/{id}` | Full detail with issues + pages |
| GET | `/api/audits/{id}/compare/{previous_id}` | Score deltas |

### Reports

| Method | Path | Format |
|---|---|---|
| GET | `/api/reports/{id}/html` | Rendered HTML dashboard |
| GET | `/api/reports/{id}/pdf` | WeasyPrint PDF |
| GET | `/api/reports/{id}/csv` | All issues as CSV |

### Users

| Method | Path | Returns |
|---|---|---|
| GET | `/api/users/me` | Current user |

---

## 9. CLI reference

```powershell
seo-audit audit URL [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--max-pages N` | 100 | Crawl cap. |
| `--performance` | off | Also call PageSpeed Insights (needs `PSI_API_KEY`). |
| `--json PATH` | — | Write structured result to disk. |

Example for CI gating (PowerShell):

```powershell
seo-audit audit https://staging.example.com --max-pages 50 --json audit.json
$score = (Get-Content audit.json | ConvertFrom-Json).scores.overall
if ($score -lt 80) {
    Write-Error "SEO score $score below threshold 80"
    exit 1
}
```

---

## 10. Scheduled & recurring audits

The Celery `beat` service runs two schedules out of the box (UTC):

| Schedule | When | What it does |
|---|---|---|
| `weekly-audits` | Monday 06:00 | Re-audits every distinct URL on file. |
| `monthly-audits` | 1st of month 06:00 | Same, monthly cadence. |

Edit [`backend/seo_audit/tasks/celery_app.py`](backend/seo_audit/tasks/celery_app.py) to add your own:

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule["daily-priority"] = {
    "task": "seo_audit.tasks.audit_tasks.run_scheduled_audits",
    "schedule": crontab(hour=2, minute=30),
    "kwargs": {"cadence": "daily"},
}
```

Trigger a one-off audit from Python:

```python
from seo_audit.tasks.audit_tasks import run_audit_task
run_audit_task.delay(42, "https://example.com", 200, True)
```

> **Native Windows note:** Celery beat works on Windows; the worker needs `--pool=solo`. Docker handles both transparently.

---

## 11. Email notifications

Set `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` in `.env`. Notifications fire automatically after each audit when:

- Broken pages (`status_404`, `status_5xx`, `broken_internal_link`) are present, **or**
- The overall score dropped ≥ 10 points vs. the previous audit of the same URL.

For Gmail, generate an **App Password** at https://myaccount.google.com/apppasswords (you must have 2FA enabled). Use that as `SMTP_PASSWORD`.

---

## 12. Database & migrations

The first time the API starts, `init_db()` creates the schema automatically — fine for dev. For production use Alembic:

```powershell
# From the project root (in your venv or via docker exec)
alembic revision --autogenerate -m "add new column"
alembic upgrade head
alembic downgrade -1
```

Via Docker:

```powershell
docker compose exec api alembic upgrade head
```

---

## 13. Extending the tool

### Add a new audit module

1. Create `backend\seo_audit\audits\my_audit.py`:

   ```python
   from ..crawler import CrawlResult
   from .base import BaseAudit, Issue, Severity

   class MyAudit(BaseAudit):
       name = "my_audit"
       category = "technical"

       def run(self, crawl: CrawlResult) -> list[Issue]:
           issues = []
           for page in crawl.pages:
               if "?utm_" in page.url:
                   issues.append(Issue(
                       code="utm_in_url",
                       severity=Severity.LOW,
                       category=self.category,
                       message="UTM parameters in canonical URL",
                       url=page.url,
                   ))
           return issues
   ```

2. Register it in [`services/audit_runner.py`](backend/seo_audit/services/audit_runner.py):

   ```python
   from ..audits.my_audit import MyAudit
   AUDIT_PIPELINE.append(MyAudit())
   ```

3. Add a recommendation in [`recommendations/library.py`](backend/seo_audit/recommendations/library.py).

### Add a new report format / frontend page

- New report → add a function in `backend\seo_audit\reporting\` and wire a route in `api\routers\reports.py`.
- New page → add route in `frontend\src\App.tsx` + new file in `frontend\src\pages\`. Copy [`Technical.tsx`](frontend/src/pages/Technical.tsx) as a template.

---

## 14. Testing

```powershell
# Inside the venv
pytest
pytest -k scoring
pytest --cov=seo_audit --cov-report=html
```

Via Docker (no venv needed):

```powershell
docker compose exec api pytest
```

Tests use in-memory SQLite — no external services required.

---

## 15. Troubleshooting (Windows-specific)

| Symptom | Fix |
|---|---|
| **`docker: command not found`** | Docker Desktop isn't installed or isn't running. Check the whale icon in the system tray. |
| **`error during connect: open //./pipe/dockerDesktopLinuxEngine`** | Docker Desktop isn't fully started. Wait for the green status or restart it. |
| **WSL 2 errors during Docker install** | Run `wsl --install` in elevated PowerShell, reboot, and re-run Docker setup. |
| **`.\.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled`** | Run once as admin: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`. |
| **`python : The term 'python' is not recognized`** | Python isn't on PATH. Reinstall and tick **"Add python.exe to PATH"**, or use `py -3.12` instead of `python`. |
| **`pip install` fails on `psycopg`** | The wheel `psycopg[binary]` should install without compilation. If it tries to compile, you're missing MSVC build tools — install **Visual Studio Build Tools** with the "Desktop development with C++" workload, **or** just use Docker. |
| **`weasyprint` crashes / `OSError: cannot load library 'libgobject…'`** | Native GTK runtime missing. Install the **GTK3 Runtime** ([link in section 1](#1-prerequisites)) and restart PowerShell. Or use Docker. |
| **Celery worker exits with `ValueError: not enough values to unpack`** | You're using the default `prefork` pool. Add `--pool=solo` on Windows. |
| **Redis won't start** | Redis has no official Windows build. Use **Memurai**, run Redis in **WSL2**, or use Docker. |
| **`Port 5432/6379/8000/3000 is already allocated`** | Another service is using the port. Find it with `Get-NetTCPConnection -LocalPort 5432`, stop it, or change the host port in `docker-compose.yml`. |
| **Frontend can't reach API in native mode** | Vite's proxy is configured for Docker hostnames. Edit `frontend\vite.config.ts` and change `"http://api:8000"` to `"http://localhost:8000"`. |
| **`Invoke-RestMethod : The remote certificate is invalid`** | Hitting an HTTPS URL with a self-signed cert. Add `-SkipCertificateCheck` (PowerShell 7+). |
| **Long path errors (`path too long`)** | Enable long paths: in elevated PowerShell run `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force` then reboot. |
| **Crawl is extremely slow** | Lower `MAX_CONCURRENCY` in `.env`, or the target site is rate-limiting. Some hosts throttle aggressively. |
| **PSI returns `null` scores** | Either `PSI_API_KEY` is missing or the URL isn't publicly reachable. PageSpeed Insights can only audit live, public URLs. |
| **`401 Missing token`** | Token expired (default 24h). Log in again. |
| **Permission errors writing to `C:\Users\…`** | Make sure the folder is in Docker Desktop's shared paths (Settings → Resources → File Sharing). |

Enable verbose logs (Docker):

```powershell
$env:LOG_LEVEL = "DEBUG"
docker compose up
```

Native:

```powershell
$env:LOG_LEVEL = "DEBUG"
uvicorn seo_audit.main:app --reload --app-dir backend
```

---

## 16. FAQ

**Do I really need Docker on Windows?**
No, but you save yourself ~5 setup steps and several known Windows-only issues (Celery, Redis, GTK for WeasyPrint). Even seasoned Python devs use Docker for this kind of multi-service stack on Windows.

**Can I use it from WSL2 instead?**
Yes — install Python/Node/Postgres/Redis inside WSL2 Ubuntu and follow the Linux instructions. Docker Desktop integrates with WSL2 automatically. Often the smoothest "native" experience on Windows.

**How many pages can it crawl?**
Tested up to 1000 pages per audit. The crawler is async with configurable concurrency. For very large sites, split into multiple audits (e.g. by section).

**Does it execute JavaScript?**
No — static HTML only. For SPAs, ensure SSR / SSG output, or expose pre-rendered routes for crawlers.

**Can I run audits without logging in?**
The CLI requires no auth. The REST API requires auth so audits are scoped per user.

**Where are the data files stored?**
- Postgres data → the Docker volume `seo_pgdata` (managed by Docker Desktop)
- Logs → stdout of each container (`docker compose logs -f <service>`)
- Generated reports → returned by the API; not persisted to disk by default

**Where do I report bugs / contribute?**
Open an issue or PR in the repository. New audit modules and recommendation entries are particularly welcome.
