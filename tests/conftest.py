"""Shared pytest fixtures — in-memory SQLite + isolated DB session per test."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Make backend/ importable and stub a SQLite URL before app modules load.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from seo_audit.db import base as db_base  # noqa: E402
from seo_audit.db import models  # noqa: F401,E402


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    db_base.Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
