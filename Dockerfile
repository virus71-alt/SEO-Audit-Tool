FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libpq-dev \
      libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi-dev \
      curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY backend ./backend
RUN pip install -e .

ENV PYTHONPATH=/app/backend
EXPOSE 8000

CMD ["uvicorn", "seo_audit.main:app", "--host", "0.0.0.0", "--port", "8000"]
