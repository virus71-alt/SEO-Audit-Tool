"""robots.txt loader using `protego` (pure-Python, cross-platform)."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx
from protego import Protego

log = logging.getLogger(__name__)


class RobotsPolicy:
    def __init__(self, parser: Protego | None, user_agent: str) -> None:
        self._parser = parser
        self._ua = user_agent

    def can_fetch(self, url: str) -> bool:
        if self._parser is None:
            return True
        return self._parser.can_fetch(url, self._ua)

    @property
    def sitemaps(self) -> list[str]:
        if self._parser is None:
            return []
        return list(self._parser.sitemaps)


async def load_robots(base_url: str, user_agent: str) -> RobotsPolicy:
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": user_agent}) as c:
            resp = await c.get(robots_url)
        if resp.status_code >= 400:
            return RobotsPolicy(None, user_agent)
        return RobotsPolicy(Protego.parse(resp.text), user_agent)
    except Exception as exc:
        log.info("robots.txt load failed url=%s err=%s", robots_url, exc)
        return RobotsPolicy(None, user_agent)
