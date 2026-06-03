"""HTTP fetcher with retries and redirect tracking."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import httpx

from ..config import get_settings

log = logging.getLogger(__name__)


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    text: str
    headers: dict[str, str]
    redirect_chain: list[tuple[str, int]] = field(default_factory=list)
    response_time_ms: int = 0
    error: str | None = None


class Fetcher:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        settings = get_settings()
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=settings.request_timeout,
            follow_redirects=False,
            headers={"User-Agent": settings.user_agent},
            http2=False,
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "Fetcher":
        return self

    async def __aexit__(self, *_exc) -> None:
        await self.close()

    async def fetch(self, url: str, *, max_redirects: int = 5) -> FetchResult:
        chain: list[tuple[str, int]] = []
        current = url
        start = time.perf_counter()
        try:
            for _ in range(max_redirects + 1):
                resp = await self._client.get(current)
                chain.append((current, resp.status_code))
                if resp.is_redirect and "location" in resp.headers:
                    location = resp.headers["location"]
                    current = str(httpx.URL(current).join(location))
                    continue
                elapsed = int((time.perf_counter() - start) * 1000)
                return FetchResult(
                    url=url,
                    final_url=current,
                    status_code=resp.status_code,
                    text=resp.text,
                    headers=dict(resp.headers),
                    redirect_chain=chain,
                    response_time_ms=elapsed,
                )
            # Exceeded max_redirects
            elapsed = int((time.perf_counter() - start) * 1000)
            return FetchResult(
                url=url,
                final_url=current,
                status_code=0,
                text="",
                headers={},
                redirect_chain=chain,
                response_time_ms=elapsed,
                error="too_many_redirects",
            )
        except httpx.HTTPError as exc:
            elapsed = int((time.perf_counter() - start) * 1000)
            log.warning("fetch failed url=%s err=%s", url, exc)
            return FetchResult(
                url=url,
                final_url=current,
                status_code=0,
                text="",
                headers={},
                redirect_chain=chain,
                response_time_ms=elapsed,
                error=str(exc),
            )
