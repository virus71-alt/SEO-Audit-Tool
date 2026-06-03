"""Technical SEO audit — status codes, redirects, indexability, HTTPS, depth, orphans."""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlparse

from ..crawler import CrawlResult
from .base import BaseAudit, Issue, Severity


class TechnicalAudit(BaseAudit):
    name = "technical"
    category = "technical"

    def run(self, crawl: CrawlResult) -> list[Issue]:
        issues: list[Issue] = []
        issues.extend(self._status_codes(crawl))
        issues.extend(self._redirects(crawl))
        issues.extend(self._indexability(crawl))
        issues.extend(self._https(crawl))
        issues.extend(self._architecture(crawl))
        return issues

    def _status_codes(self, crawl: CrawlResult) -> list[Issue]:
        out: list[Issue] = []
        for page in crawl.pages:
            sc = page.status_code
            if sc == 404:
                out.append(
                    Issue(
                        code="status_404",
                        severity=Severity.HIGH,
                        category=self.category,
                        message="Page returns 404 Not Found",
                        url=page.url,
                    )
                )
            elif sc and 500 <= sc < 600:
                out.append(
                    Issue(
                        code="status_5xx",
                        severity=Severity.CRITICAL,
                        category=self.category,
                        message=f"Page returns {sc} server error",
                        url=page.url,
                    )
                )
            elif sc == 0:
                out.append(
                    Issue(
                        code="status_unreachable",
                        severity=Severity.HIGH,
                        category=self.category,
                        message=f"Page unreachable: {page.error or 'unknown error'}",
                        url=page.url,
                    )
                )
            # Soft 404: 200 OK with very thin body and 'not found' wording
            if sc == 200 and page.parsed and page.parsed.word_count < 50:
                body = (page.parsed.text or "").lower()
                if "not found" in body or "page does not exist" in body:
                    out.append(
                        Issue(
                            code="soft_404",
                            severity=Severity.MEDIUM,
                            category=self.category,
                            message="Suspected soft 404 (200 OK but reads as not-found)",
                            url=page.url,
                        )
                    )
        return out

    def _redirects(self, crawl: CrawlResult) -> list[Issue]:
        out: list[Issue] = []
        for page in crawl.pages:
            redirects = [c for c in page.redirect_chain if 300 <= c[1] < 400]
            if len(redirects) >= 2:
                out.append(
                    Issue(
                        code="redirect_chain",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message=f"Redirect chain of length {len(redirects)}",
                        url=page.url,
                        details={"chain": page.redirect_chain},
                    )
                )
            urls_in_chain = [c[0] for c in page.redirect_chain]
            if len(urls_in_chain) != len(set(urls_in_chain)):
                out.append(
                    Issue(
                        code="redirect_loop",
                        severity=Severity.HIGH,
                        category=self.category,
                        message="Redirect loop detected",
                        url=page.url,
                        details={"chain": page.redirect_chain},
                    )
                )
        return out

    def _indexability(self, crawl: CrawlResult) -> list[Issue]:
        out: list[Issue] = []
        canonicals_to_urls: dict[str, list[str]] = defaultdict(list)
        for page in crawl.pages:
            if not page.parsed:
                continue
            robots = (page.parsed.meta_robots or "").lower()
            if "noindex" in robots:
                out.append(
                    Issue(
                        code="meta_noindex",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message="Page is set to noindex",
                        url=page.url,
                    )
                )
            canonical = page.parsed.canonical
            if canonical:
                canonicals_to_urls[canonical].append(page.url)
                if canonical != page.final_url and canonical != page.url:
                    out.append(
                        Issue(
                            code="canonical_mismatch",
                            severity=Severity.LOW,
                            category=self.category,
                            message="Canonical points to a different URL than the page itself",
                            url=page.url,
                            details={"canonical": canonical},
                        )
                    )
        for canonical, urls in canonicals_to_urls.items():
            if len(urls) > 1:
                out.append(
                    Issue(
                        code="duplicate_canonical",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message=f"{len(urls)} pages share the same canonical URL",
                        url=canonical,
                        details={"pages": urls[:10]},
                    )
                )
        return out

    def _https(self, crawl: CrawlResult) -> list[Issue]:
        out: list[Issue] = []
        has_https = any(p.final_url.startswith("https://") for p in crawl.pages)
        has_http = any(p.final_url.startswith("http://") for p in crawl.pages)
        if has_http and has_https:
            out.append(
                Issue(
                    code="mixed_protocol",
                    severity=Severity.HIGH,
                    category=self.category,
                    message="Site serves both HTTP and HTTPS URLs",
                )
            )
        if has_http and not has_https:
            out.append(
                Issue(
                    code="no_https",
                    severity=Severity.CRITICAL,
                    category=self.category,
                    message="Site is served over HTTP without HTTPS",
                )
            )
        for page in crawl.pages:
            if page.parsed and page.parsed.has_https_mixed:
                out.append(
                    Issue(
                        code="mixed_content",
                        severity=Severity.HIGH,
                        category=self.category,
                        message="HTTPS page loads HTTP resources (mixed content)",
                        url=page.url,
                    )
                )
        return out

    def _architecture(self, crawl: CrawlResult) -> list[Issue]:
        out: list[Issue] = []
        # Deep pages
        for page in crawl.pages:
            if page.depth > 4:
                out.append(
                    Issue(
                        code="deep_page",
                        severity=Severity.LOW,
                        category=self.category,
                        message=f"Page is {page.depth} clicks from the homepage",
                        url=page.url,
                    )
                )
        # Orphan pages: in sitemap but never linked internally
        linked: set[str] = set()
        for page in crawl.pages:
            if page.parsed:
                for link in page.parsed.internal_links:
                    linked.add(link.href.rstrip("/"))
        sitemap_set = {u.rstrip("/") for u in crawl.sitemap_urls}
        for url in sitemap_set - linked:
            if any(p.url.rstrip("/") == url for p in crawl.pages):
                out.append(
                    Issue(
                        code="orphan_page",
                        severity=Severity.MEDIUM,
                        category=self.category,
                        message="Page is in sitemap but has no internal links pointing to it",
                        url=url,
                    )
                )
        # Broken internal links — links that resolve to 4xx/5xx in our crawl
        status_by_url = {p.url.rstrip("/"): p.status_code for p in crawl.pages}
        seen_broken: set[tuple[str, str]] = set()
        for page in crawl.pages:
            if not page.parsed:
                continue
            for link in page.parsed.internal_links:
                target = link.href.rstrip("/")
                code = status_by_url.get(target)
                if code and code >= 400 and (page.url, target) not in seen_broken:
                    seen_broken.add((page.url, target))
                    out.append(
                        Issue(
                            code="broken_internal_link",
                            severity=Severity.HIGH,
                            category=self.category,
                            message=f"Internal link to {target} returns {code}",
                            url=page.url,
                            details={"target": target, "status": code},
                        )
                    )
        return out
