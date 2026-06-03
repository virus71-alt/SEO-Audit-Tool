from seo_audit.audits.base import Issue, Severity
from seo_audit.recommendations import RecommendationEngine


def test_enrich_attaches_recommendation():
    issues = [Issue(code="missing_title", severity=Severity.HIGH, category="onpage", message="m")]
    enriched = RecommendationEngine().enrich(issues)
    assert enriched[0].recommendation
    assert enriched[0].impact


def test_prioritized_orders_by_severity():
    issues = [
        Issue(code="a", severity=Severity.LOW, category="x", message="m"),
        Issue(code="b", severity=Severity.CRITICAL, category="x", message="m"),
        Issue(code="c", severity=Severity.HIGH, category="x", message="m"),
    ]
    ordered = RecommendationEngine().prioritized(issues)
    assert [i.severity.value for i in ordered[:3]] == ["critical", "high", "low"]
