from seo_audit.crawler.parser import parse_html

HTML = """
<!doctype html><html lang="en"><head>
<title>Test Page</title>
<meta name="description" content="Hello world">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta property="og:title" content="Test">
<meta property="og:image" content="https://example.com/x.png">
<link rel="canonical" href="https://example.com/page">
<script type="application/ld+json">{"@type":"Article","headline":"Hi"}</script>
</head><body>
<h1>Welcome</h1>
<h2>Section</h2>
<p>Hello world this is content for testing.</p>
<img src="/a.png" alt="alt text" width="100" height="100">
<img src="/b.png">
<a href="/about">About</a>
<a href="https://other.com/x">External</a>
</body></html>
"""


def test_parse_html_extracts_signals():
    p = parse_html("https://example.com/page", HTML)
    assert p.title == "Test Page"
    assert p.meta_description == "Hello world"
    assert p.canonical == "https://example.com/page"
    assert p.viewport.startswith("width=device-width")
    assert p.h1 == ["Welcome"]
    assert p.h2 == ["Section"]
    assert len(p.images) == 2
    assert p.images[0].alt == "alt text"
    assert p.images[1].alt is None
    assert any(l.is_internal for l in p.internal_links)
    assert any(not l.is_internal for l in p.external_links)
    assert p.open_graph.get("og:title") == "Test"
    assert p.schema_blocks and p.schema_blocks[0]["@type"] == "Article"
