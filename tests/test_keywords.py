from seo_audit.audits.keywords import extract_keywords


def test_extract_keywords_returns_top_terms():
    text = "python python python is great. python rocks." * 5
    kw = extract_keywords(text, top_n=5)
    assert kw["top_unigrams"]
    top = kw["top_unigrams"][0]
    assert top["term"] == "python"
    assert top["count"] >= 15
