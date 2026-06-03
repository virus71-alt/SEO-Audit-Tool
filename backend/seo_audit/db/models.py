"""SQLAlchemy ORM models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    audits: Mapped[list["Audit"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    url: Mapped[str] = mapped_column(String(2048), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|running|done|failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    onpage_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    performance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    content_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    mobile_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped[User | None] = relationship(back_populates="audits")
    pages: Mapped[list["Page"]] = relationship(back_populates="audit", cascade="all, delete-orphan")
    issues: Mapped[list["Issue"]] = relationship(back_populates="audit", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(2048), index=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    h1: Mapped[list | None] = mapped_column(JSON, nullable=True)
    h2: Mapped[list | None] = mapped_column(JSON, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[list | None] = mapped_column(JSON, nullable=True)
    internal_links: Mapped[list | None] = mapped_column(JSON, nullable=True)
    external_links: Mapped[list | None] = mapped_column(JSON, nullable=True)
    schema_blocks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    open_graph: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    twitter: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    audit: Mapped[Audit] = relationship(back_populates="pages")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)  # critical|high|medium|low|info
    category: Mapped[str] = mapped_column(String(32), index=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    example: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    audit: Mapped[Audit] = relationship(back_populates="issues")
