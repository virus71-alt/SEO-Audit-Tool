from seo_audit.audits.onpage import OnPageAudit
from seo_audit.audits.technical import TechnicalAudit
from seo_audit.audits.mobile import MobileAudit
from seo_audit.crawler import CrawlResult
from seo_audit.crawler.crawler import PageData
from seo_audit.crawler.parser import ParsedPage


def make_page(url: str, **kw) -> PageData:
    p = ParsedPage(url=url, **{k: v for k, v in kw.items() if hasattr(ParsedPage, k)})
    return PageData(
        url=url,
        final_url=url,
        status_code=kw.get("status_code", 200),
        depth=kw.get("depth", 0),
        redirect_chain=kw.get("redirect_chain", []),
        response_time_ms=10,
        parsed=p,
    )


def test_technical_detects_404_and_5xx():
    pages = [
        make_page("https://a.com/x", status_code=404),
        make_page("https://a.com/y", status_code=503),
    ]
    issues = TechnicalAudit().run(CrawlResult(base_url="https://a.com", pages=pages))
    codes = {i.code for i in issues}
    assert "status_404" in codes
    assert "status_5xx" in codes


def test_onpage_detects_missing_title_and_h1():
    pages = [make_page("https://a.com/x")]
    pages[0].parsed.title = None
    pages[0].parsed.meta_description = None
    issues = OnPageAudit().run(CrawlResult(base_url="https://a.com", pages=pages))
    codes = {i.code for i in issues}
    assert "missing_title" in codes
    assert "missing_meta_description" in codes
    assert "missing_h1" in codes


def test_mobile_detects_missing_viewport():
    pages = [make_page("https://a.com/x")]
    pages[0].parsed.viewport = None
    issues = MobileAudit().run(CrawlResult(base_url="https://a.com", pages=pages))
    assert any(i.code == "missing_viewport" for i in issues)
