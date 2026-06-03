"""Per-issue recommendation library.

Each entry maps an Issue.code to (impact, recommendation, example) text. The
RecommendationEngine consults this map to enrich raw issues with actionable fixes.
"""
from __future__ import annotations

from typing import TypedDict


class Recommendation(TypedDict):
    impact: str
    recommendation: str
    example: str


RECOMMENDATIONS: dict[str, Recommendation] = {
    # --- Status codes & redirects ---
    "status_404": {
        "impact": "Wastes crawl budget and confuses users; broken links lose link equity.",
        "recommendation": "Either restore the page, or 301-redirect to the closest relevant URL. If intentional, remove inbound links.",
        "example": "RewriteRule ^/old-page$ /new-page [R=301,L]",
    },
    "status_5xx": {
        "impact": "Search engines may de-index pages that consistently return 5xx errors.",
        "recommendation": "Investigate server logs, fix the underlying error, and add monitoring so regressions page on-call.",
        "example": "tail -f /var/log/nginx/error.log",
    },
    "status_unreachable": {
        "impact": "Pages that time out are effectively invisible to search engines.",
        "recommendation": "Check DNS, firewall rules, and origin response times; ensure the bot's UA is not blocked.",
        "example": "curl -I -A 'SEOAuditBot/1.0' https://example.com/page",
    },
    "redirect_chain": {
        "impact": "Each hop dilutes link equity and slows crawling and page load.",
        "recommendation": "Collapse the chain so every internal link points directly to the final URL with one 301.",
        "example": "/a → /b → /c   ⇒   /a → /c",
    },
    "redirect_loop": {
        "impact": "Pages stuck in a loop are never indexed.",
        "recommendation": "Break the cycle by removing the offending redirect rule.",
        "example": "",
    },
    "soft_404": {
        "impact": "Soft 404s bloat the index and waste crawl budget.",
        "recommendation": "Return a real 404/410 status, or add substantive content if the URL should rank.",
        "example": "HTTP/1.1 404 Not Found",
    },
    # --- Indexability ---
    "meta_noindex": {
        "impact": "Noindex pages will not appear in search results.",
        "recommendation": "Remove the noindex directive if the page should rank; otherwise also add it to robots.txt to save crawl budget.",
        "example": '<meta name="robots" content="index,follow">',
    },
    "canonical_mismatch": {
        "impact": "Conflicting canonicals can prevent the intended URL from ranking.",
        "recommendation": "Make the canonical match the URL you want to rank; use absolute, HTTPS URLs.",
        "example": '<link rel="canonical" href="https://example.com/page">',
    },
    "duplicate_canonical": {
        "impact": "Multiple pages canonicalizing to the same URL can lose unique indexing.",
        "recommendation": "Audit whether each page should be self-canonical or merged.",
        "example": "",
    },
    # --- HTTPS ---
    "no_https": {
        "impact": "Browsers flag HTTP pages as insecure and Google uses HTTPS as a ranking signal.",
        "recommendation": "Install a TLS certificate (Let's Encrypt is free) and 301-redirect all HTTP to HTTPS.",
        "example": "Let's Encrypt: certbot --nginx -d example.com",
    },
    "mixed_protocol": {
        "impact": "Mixed HTTP/HTTPS URLs cause duplicate content and security warnings.",
        "recommendation": "Force HTTPS at the edge and update all internal links to absolute HTTPS URLs.",
        "example": 'return 301 https://$host$request_uri;',
    },
    "mixed_content": {
        "impact": "Browsers may block insecure subresources, breaking the page and harming UX.",
        "recommendation": "Update all asset URLs to https:// (or use protocol-relative // URLs).",
        "example": '<script src="https://cdn.example.com/lib.js"></script>',
    },
    # --- Architecture ---
    "deep_page": {
        "impact": "Pages buried >3 clicks from the homepage are crawled less often.",
        "recommendation": "Add contextual or category links so important pages are reachable in ≤3 clicks.",
        "example": "",
    },
    "orphan_page": {
        "impact": "Without inbound links, the page won't be discovered by crawlers or pass authority.",
        "recommendation": "Link to the page from at least one relevant parent page.",
        "example": "",
    },
    "broken_internal_link": {
        "impact": "Broken links frustrate users and waste crawl budget.",
        "recommendation": "Update or remove the link to point to a live URL.",
        "example": "",
    },
    # --- On-page ---
    "missing_title": {
        "impact": "Without a title, search engines fabricate one — often poorly — hurting CTR.",
        "recommendation": "Add a unique 50-60 character <title> that contains the primary keyword.",
        "example": "<title>Best Running Shoes 2026 | Acme</title>",
    },
    "title_too_short": {
        "impact": "Short titles miss ranking and CTR opportunities.",
        "recommendation": "Expand to 50-60 chars, naturally including the primary keyword and a value prop.",
        "example": "",
    },
    "title_too_long": {
        "impact": "Long titles get truncated in SERPs.",
        "recommendation": "Tighten to under 60 chars; lead with the most important keywords.",
        "example": "",
    },
    "duplicate_title": {
        "impact": "Duplicate titles split ranking signals across pages.",
        "recommendation": "Make every title unique and specific to that page's intent.",
        "example": "",
    },
    "missing_meta_description": {
        "impact": "No meta description = lower CTR and Google writing its own snippet.",
        "recommendation": "Add a unique 140-160 char description with primary keyword and a call to action.",
        "example": '<meta name="description" content="...">',
    },
    "meta_too_short": {
        "impact": "Short descriptions miss CTR opportunities.",
        "recommendation": "Aim for 140-160 chars and include the primary keyword early.",
        "example": "",
    },
    "meta_too_long": {
        "impact": "Long descriptions get truncated.",
        "recommendation": "Trim to under 160 chars.",
        "example": "",
    },
    "duplicate_meta": {
        "impact": "Duplicate descriptions confuse users and waste SERP real estate.",
        "recommendation": "Write a unique description for each page.",
        "example": "",
    },
    "missing_h1": {
        "impact": "Search engines and screen readers rely on H1 to understand page topic.",
        "recommendation": "Add a single, descriptive H1 that includes the primary keyword.",
        "example": "<h1>Beginner's Guide to SEO</h1>",
    },
    "multiple_h1": {
        "impact": "Multiple H1s dilute the page's topical focus.",
        "recommendation": "Use exactly one H1 per page; demote others to H2.",
        "example": "",
    },
    "heading_skip": {
        "impact": "Skipping heading levels hurts accessibility and topical clarity.",
        "recommendation": "Use headings in order: H1 → H2 → H3 without jumping levels.",
        "example": "",
    },
    # --- Content ---
    "thin_content": {
        "impact": "Pages under ~300 words rarely rank for competitive queries.",
        "recommendation": "Expand with examples, FAQs, or supporting depth — or noindex if the page isn't meant to rank.",
        "example": "",
    },
    "duplicate_content": {
        "impact": "Duplicate pages compete with themselves for rankings.",
        "recommendation": "Canonicalize duplicates to a single authoritative URL or consolidate them.",
        "example": '<link rel="canonical" href="https://example.com/main">',
    },
    "keyword_stuffing": {
        "impact": "Over-optimization can trigger spam classifiers and feels unnatural to readers.",
        "recommendation": "Reduce keyword density to under 3%; use synonyms and related entities (LSI).",
        "example": "",
    },
    "keyword_not_in_title": {
        "impact": "Title and H1 are the strongest on-page ranking signals.",
        "recommendation": "Include the page's primary keyword in both the title and H1.",
        "example": "",
    },
    # --- Images ---
    "image_missing_alt": {
        "impact": "Missing alt text hurts accessibility and image search rankings.",
        "recommendation": "Add concise descriptive alt text (decorative images may use alt=\"\").",
        "example": '<img src="..." alt="red running shoe side view">',
    },
    "image_empty_alt": {
        "impact": "Empty alt is only correct for purely decorative images.",
        "recommendation": "If the image conveys information, add real alt text.",
        "example": "",
    },
    "image_missing_dimensions": {
        "impact": "Without dimensions, the layout shifts as images load (high CLS).",
        "recommendation": "Set explicit width and height attributes (or CSS aspect-ratio).",
        "example": '<img src="..." width="800" height="600">',
    },
    # --- Schema ---
    "missing_schema": {
        "impact": "Without structured data, rich results (FAQs, breadcrumbs, ratings) aren't eligible.",
        "recommendation": "Add JSON-LD markup appropriate to the page type (Article, Product, FAQPage, etc.).",
        "example": '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article",...}</script>',
    },
    "schema_no_type": {
        "impact": "Schema without @type cannot be interpreted.",
        "recommendation": "Add an explicit @type from schema.org.",
        "example": '"@type": "Article"',
    },
    "schema_missing_fields": {
        "impact": "Missing required fields disqualify the page from rich results.",
        "recommendation": "Add the missing properties per Google's structured data documentation.",
        "example": "",
    },
    # --- Social ---
    "missing_og": {
        "impact": "Missing OG tags cause ugly social shares with no image or summary.",
        "recommendation": "Add og:title, og:description, og:image, og:url to every public page.",
        "example": '<meta property="og:title" content="...">',
    },
    "missing_twitter_card": {
        "impact": "Twitter falls back to a plain link without a card.",
        "recommendation": "Add twitter:card='summary_large_image' plus title/description/image.",
        "example": '<meta name="twitter:card" content="summary_large_image">',
    },
    # --- Links ---
    "internal_nofollow": {
        "impact": "Nofollow on internal links wastes link equity.",
        "recommendation": "Remove rel=nofollow from internal links.",
        "example": "",
    },
    "link_redirects": {
        "impact": "Linking through redirects slows users and wastes crawl budget.",
        "recommendation": "Update the href to the final destination URL.",
        "example": "",
    },
    "no_inbound_links": {
        "impact": "Pages with no internal links rely solely on the sitemap for discovery.",
        "recommendation": "Add at least one contextual internal link from a related page.",
        "example": "",
    },
    # --- Mobile ---
    "missing_viewport": {
        "impact": "Mobile devices won't scale the page, breaking the layout.",
        "recommendation": "Add the viewport meta tag.",
        "example": '<meta name="viewport" content="width=device-width, initial-scale=1">',
    },
    "bad_viewport": {
        "impact": "Without width=device-width, the page won't be responsive.",
        "recommendation": "Use the standard viewport directive.",
        "example": '<meta name="viewport" content="width=device-width, initial-scale=1">',
    },
    # --- Performance ---
    "slow_response": {
        "impact": "Slow TTFB delays everything downstream; user bounce rates spike >3s.",
        "recommendation": "Add caching/CDN, optimize DB queries, and consider a faster origin.",
        "example": "",
    },
    "lcp_slow": {
        "impact": "LCP is a Core Web Vital; >2.5s harms rankings and conversions.",
        "recommendation": "Optimize hero images (preload, modern formats), reduce render-blocking JS/CSS.",
        "example": '<link rel="preload" as="image" href="/hero.webp">',
    },
    "cls_high": {
        "impact": "Layout shift is a Core Web Vital; users mis-click and bounce.",
        "recommendation": "Reserve space for images/ads with width/height or aspect-ratio.",
        "example": "",
    },
    "fcp_slow": {
        "impact": "Slow first paint feels unresponsive.",
        "recommendation": "Inline critical CSS, defer non-essential JS, use HTTP/3.",
        "example": "",
    },
    "ttfb_slow": {
        "impact": "High TTFB delays every other metric.",
        "recommendation": "Cache at the edge, reduce origin work, use a CDN.",
        "example": "",
    },
}


def get(code: str) -> Recommendation | None:
    return RECOMMENDATIONS.get(code)
