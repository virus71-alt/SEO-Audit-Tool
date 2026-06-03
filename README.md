# SEO Audit Tool

A production-quality, modular SEO audit platform written in Python (FastAPI) with a React frontend. Performs comprehensive technical, on-page, content, performance, mobile, structured-data, link, and keyword analysis comparable in scope to Ahrefs Site Audit / SEMrush / Screaming Frog / Google Search Console.

## Highlights

- Async crawler (1000+ pages) with robots.txt, sitemap, canonical, redirect handling
- 10+ specialized audit modules
- Weighted SEO scoring (Technical 30 / On-Page 25 / Performance 20 / Content 15 / Mobile 10)
- AI recommendation engine with severity, impact, and fix templates
- HTML dashboard + PDF + CSV reports
- React + Tailwind frontend (dark/light, responsive, modern SaaS look)
- PostgreSQL persistence with historical comparison
- Celery + Redis for scheduled / weekly / monthly audits
- JWT authentication
- Email notifications (broken pages, score drops, SSL expiry)
- Docker Compose deployment

## Quick start

```bash
git clone <repo> && cd SEO
cp .env.example .env       # set DB / Redis / SMTP / PSI_API_KEY
docker compose up --build
```

- API: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Worker logs: `docker compose logs -f worker`

## Run an audit (CLI)

```bash
python -m seo_audit.cli audit https://example.com --max-pages 200
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md).

## License

MIT
# SEO-Audit-Tool
