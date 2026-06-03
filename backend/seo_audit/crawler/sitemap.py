"""Sitemap loader — handles sitemap indexes and regular sitemaps."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx
from lxml import etree

log = logging.getLogger(__name__)

_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


async def discover_sitemaps(base_url: str, hinted: list[str], user_agent: str) -> list[str]:
    seen: set[str] = set(hinted)
    parsed = urlparse(base_url)
    seen.add(f"{parsed.scheme}://{parsed.netloc}/sitemap.xml")
    seen.add(f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml")
    return list(seen)


async def fetch_sitemap_urls(sitemap_url: str, user_agent: str, max_urls: int = 5000) -> list[str]:
    found: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": user_agent}) as client:
            await _walk(client, sitemap_url, found, max_urls, depth=0)
    except Exception as exc:
        log.info("sitemap fetch failed url=%s err=%s", sitemap_url, exc)
    return found


async def _walk(
    client: httpx.AsyncClient,
    url: str,
    found: list[str],
    max_urls: int,
    depth: int,
) -> None:
    if depth > 3 or len(found) >= max_urls:
        return
    try:
        resp = await client.get(url)
        if resp.status_code >= 400:
            return
        root = etree.fromstring(resp.content)
    except Exception:
        return

    tag = etree.QName(root.tag).localname
    if tag == "sitemapindex":
        for loc in root.xpath("//sm:sitemap/sm:loc/text()", namespaces=_NS):
            await _walk(client, str(loc).strip(), found, max_urls, depth + 1)
    elif tag == "urlset":
        for loc in root.xpath("//sm:url/sm:loc/text()", namespaces=_NS):
            if len(found) >= max_urls:
                return
            found.append(str(loc).strip())
