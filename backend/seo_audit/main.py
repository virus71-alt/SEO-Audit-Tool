"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import audits, auth, reports, users
from .config import get_settings
from .db.base import init_db
from .logging_setup import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SEO Audit API",
        version="0.1.0",
        description="Production-grade SEO auditing platform.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(audits.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    return app


app = create_app()
