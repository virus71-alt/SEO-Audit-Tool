"""Application-specific exceptions."""
from __future__ import annotations


class SEOAuditError(Exception):
    """Base error for the application."""


class CrawlError(SEOAuditError):
    """Raised when crawling fails irrecoverably."""


class AuditError(SEOAuditError):
    """Raised when an audit module fails."""


class AuthError(SEOAuditError):
    """Authentication / authorization failure."""
