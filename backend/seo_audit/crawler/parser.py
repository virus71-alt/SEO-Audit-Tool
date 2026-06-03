"""HTML parser extracting all SEO-relevant signals from a page."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup


@dataclass
class ImageInfo:
    src: str
    alt: str | None
    width: str | None = None
    height: str | None = None


@dataclass
class LinkInfo:
    href: str
    text: str
    rel: list[str] = field(default_factory=list)
    is_internal: bool = False


@dataclass
class ParsedPage:
    url: str
    title: str | None = None
    meta_description: str | None = None
    meta_robots: str | None = None
    canonical: str | None = None
    lang: str | None = None
    viewport: str | None = None
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    h3: list[str] = field(default_factory=list)
    headings_order: list[tuple[int, str]] = field(default_factory=list)
    text: str = ""
    word_count: int = 0
    images: list[ImageInfo] = field(default_factory=list)
    internal_links: list[LinkInfo] = field(default_factory=list)
    external_links: list[LinkInfo] = field(default_factory=list)
    schema_blocks: list[dict] = field(default_factory=list)
    open_graph: dict[str, str] = field(default_factory=dict)
    twitter: dict[str, str] = field(default_factory=dict)
    has_https_mixed: bool = False


def _same_host(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()
    except Exception:
        return False


def parse_html(url: str, html: str) -> ParsedPage:
    soup = BeautifulSoup(html, "lxml")
    page = ParsedPage(url=url)

    if soup.title and soup.title.string:
        page.title = soup.title.string.strip()

    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        prop = (meta.get("property") or "").lower()
        content = meta.get("content") or ""
        if name == "description":
            page.meta_description = content.strip()
        elif name == "robots":
            page.meta_robots = content.strip()
        elif name == "viewport":
            page.viewport = content.strip()
        elif prop.startswith("og:"):
            page.open_graph[prop] = content.strip()
        elif name.startswith("twitter:"):
            page.twitter[name] = content.strip()

    link_canonical = soup.find("link", rel=lambda v: v and "canonical" in v)
    if link_canonical and link_canonical.get("href"):
        page.canonical = urljoin(url, link_canonical["href"])

    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        page.lang = html_tag["lang"].strip()

    for level, attr in [(1, "h1"), (2, "h2"), (3, "h3")]:
        for h in soup.find_all(attr):
            text = h.get_text(strip=True)
            if not text:
                continue
            if level == 1:
                page.h1.append(text)
            elif level == 2:
                page.h2.append(text)
            else:
                page.h3.append(text)
            page.headings_order.append((level, text))

    # Also pick up h4-h6 for hierarchy checks
    for lvl in (4, 5, 6):
        for h in soup.find_all(f"h{lvl}"):
            t = h.get_text(strip=True)
            if t:
                page.headings_order.append((lvl, t))

    body_text = soup.get_text(" ", strip=True)
    page.text = body_text
    page.word_count = len(re.findall(r"\w+", body_text))

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        full = urljoin(url, src)
        page.images.append(
            ImageInfo(
                src=full,
                alt=img.get("alt"),
                width=img.get("width"),
                height=img.get("height"),
            )
        )

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        full = urldefrag(urljoin(url, href))[0]
        link = LinkInfo(
            href=full,
            text=a.get_text(strip=True)[:200],
            rel=(a.get("rel") or []) if isinstance(a.get("rel"), list) else [a.get("rel") or ""],
            is_internal=_same_host(url, full),
        )
        if link.is_internal:
            page.internal_links.append(link)
        else:
            page.external_links.append(link)

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
            page.schema_blocks.append(data)
        except Exception:
            continue

    if url.startswith("https://"):
        for tag, attr in [("img", "src"), ("script", "src"), ("link", "href"), ("iframe", "src")]:
            for el in soup.find_all(tag):
                val = el.get(attr)
                if val and val.startswith("http://"):
                    page.has_https_mixed = True
                    break
            if page.has_https_mixed:
                break

    return page
