"""Async BFS crawler honoring robots.txt, sitemap, canonicals, and dedup."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from urllib.parse import urldefrag, urljoin, urlparse

from ..config import get_settings
from .fetcher import FetchResult, Fetcher
from .parser import ParsedPage, parse_html
from .robots import RobotsPolicy, load_robots
from .sitemap import discover_sitemaps, fetch_sitemap_urls

log = logging.getLogger(__name__)


@dataclass
class PageData:
    url: str
    final_url: str
    status_code: int
    depth: int
    redirect_chain: list[tuple[str, int]]
    response_time_ms: int
    parsed: ParsedPage | None = None
    error: str | None = None


@dataclass
class CrawlResult:
    base_url: str
    pages: list[PageData] = field(default_factory=list)
    robots_loaded: bool = False
    sitemap_urls: list[str] = field(default_factory=list)


class Crawler:
    def __init__(
        self,
        base_url: str,
        max_pages: int = 200,
        max_depth: int = 10,
        concurrency: int | None = None,
        respect_robots: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.respect_robots = respect_robots
        settings = get_settings()
        self.concurrency = concurrency or settings.max_concurrency
        self._ua = settings.user_agent

        self._seen: set[str] = set()
        self._queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        self._results: list[PageData] = []
        self._sem = asyncio.Semaphore(self.concurrency)
        self._robots: RobotsPolicy | None = None
        self._base_netloc = urlparse(self.base_url).netloc.lower()

    def _normalize(self, url: str) -> str:
        return urldefrag(url)[0].rstrip("/") or url

    def _is_internal(self, url: str) -> bool:
        try:
            return urlparse(url).netloc.lower() == self._base_netloc
        except Exception:
            return False

    async def crawl(self) -> CrawlResult:
        result = CrawlResult(base_url=self.base_url)

        self._robots = await load_robots(self.base_url, self._ua)
        result.robots_loaded = self._robots._parser is not None

        seed_urls = [self.base_url]
        sitemaps = await discover_sitemaps(self.base_url, self._robots.sitemaps, self._ua)
        for sm in sitemaps:
            urls = await fetch_sitemap_urls(sm, self._ua, max_urls=self.max_pages)
            seed_urls.extend(u for u in urls if self._is_internal(u))
            result.sitemap_urls.extend(urls)

        for u in seed_urls:
            n = self._normalize(u)
            if n not in self._seen:
                self._seen.add(n)
                await self._queue.put((n, 0))

        async with Fetcher() as fetcher:
            workers = [asyncio.create_task(self._worker(fetcher)) for _ in range(self.concurrency)]
            await self._queue.join()
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

        result.pages = self._results
        return result

    async def _worker(self, fetcher: Fetcher) -> None:
        while True:
            try:
                url, depth = await self._queue.get()
            except asyncio.CancelledError:
                return
            try:
                if len(self._results) >= self.max_pages:
                    return
                await self._process(url, depth, fetcher)
            finally:
                self._queue.task_done()

    async def _process(self, url: str, depth: int, fetcher: Fetcher) -> None:
        if self.respect_robots and self._robots and not self._robots.can_fetch(url):
            log.info("blocked by robots: %s", url)
            return

        async with self._sem:
            res: FetchResult = await fetcher.fetch(url)

        parsed: ParsedPage | None = None
        if res.text and 200 <= res.status_code < 400:
            try:
                parsed = parse_html(res.final_url, res.text)
            except Exception as exc:  # parsing should never block crawling
                log.warning("parse failed url=%s err=%s", url, exc)

        self._results.append(
            PageData(
                url=url,
                final_url=res.final_url,
                status_code=res.status_code,
                depth=depth,
                redirect_chain=res.redirect_chain,
                response_time_ms=res.response_time_ms,
                parsed=parsed,
                error=res.error,
            )
        )

        if parsed and depth < self.max_depth and len(self._results) < self.max_pages:
            for link in parsed.internal_links:
                next_url = self._normalize(link.href)
                if next_url in self._seen:
                    continue
                if not self._is_internal(next_url):
                    continue
                self._seen.add(next_url)
                await self._queue.put((next_url, depth + 1))
