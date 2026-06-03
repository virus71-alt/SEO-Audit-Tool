from seo_audit.audits.base import Issue, Severity
from seo_audit.scoring import Scorer


def test_score_starts_at_100():
    score = Scorer().score([])
    assert score.overall == 100.0
    assert score.technical == 100.0


def test_score_penalizes_severity():
    issues = [
        Issue(code="x", severity=Severity.CRITICAL, category="technical", message="m"),
        Issue(code="y", severity=Severity.HIGH, category="onpage", message="m"),
        Issue(code="z", severity=Severity.LOW, category="content", message="m"),
    ]
    score = Scorer().score(issues)
    assert score.technical < 100
    assert score.onpage < 100
    assert score.content < 100
    assert 0 <= score.overall <= 100


def test_severity_counts():
    issues = [
        Issue(code="x", severity=Severity.CRITICAL, category="technical", message="m"),
        Issue(code="x", severity=Severity.CRITICAL, category="technical", message="m"),
        Issue(code="y", severity=Severity.LOW, category="content", message="m"),
    ]
    score = Scorer().score(issues)
    assert score.issues_by_severity["critical"] == 2
    assert score.issues_by_severity["low"] == 1
