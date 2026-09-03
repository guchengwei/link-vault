import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _payload(html: str) -> list[dict]:
    match = re.search(r"window\.BOOKMARKS=(.*?);</script>", html)
    assert match
    return json.loads(match.group(1))


def _write_bundle(content_dir: Path, month: str, slug: str, document: dict, public_url: str) -> None:
    item_dir = content_dir / month / slug
    item_dir.mkdir(parents=True)
    (item_dir / "document.json").write_text(json.dumps(document), encoding="utf-8")
    (item_dir / "index.md").write_text(document.get("markdown", "# Saved\n\nA useful opening paragraph."), encoding="utf-8")
    (item_dir / "publish.json").write_text(
        json.dumps(
            {
                "published": True,
                "public_url": public_url,
                "target": {
                    "site_path": f"site/d/{slug}/index.html",
                    "bundle_path": f"content/{month}/{slug}",
                },
            }
        ),
        encoding="utf-8",
    )


def test_build_homepage_index_creates_working_bookmark_surface(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    _write_bundle(
        content_dir,
        "2026-04",
        "x-123-example",
        {
            "title": "Example Saved Post",
            "source_type": "x",
            "source_url": "https://x.com/example/status/123",
            "author_handle": "example",
            "created_at": "2026-04-05T12:00:00Z",
        },
        "https://guchengwei.github.io/link-vault/d/x-123-example/",
    )

    output_path = build_homepage_index(content_dir=content_dir, site_dir=site_dir)

    assert output_path == site_dir / "index.html"
    assert (site_dir / "assets" / "home.css").is_file()
    assert (site_dir / "assets" / "home.js").is_file()
    html = output_path.read_text(encoding="utf-8")
    assert 'id="search-input"' in html
    assert 'id="source-filters"' in html
    records = _payload(html)
    assert records == [
        {
            "id": "x-123-example",
            "title": "Example Saved Post",
            "source": "x",
            "author": "@example",
            "date": "2026-04-05",
            "domain": "x.com",
            "url": "d/x-123-example/",
            "sourceUrl": "https://x.com/example/status/123",
            "excerpt": "Saved A useful opening paragraph.",
            "image": "",
        }
    ]


def test_homepage_payload_contains_all_sources_newest_first(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    fixtures = [
        ("2026-04", "x-123", "April X Post", "x", "2026-04-05T12:00:00Z"),
        ("2026-04", "web-hello", "April Web Post", "web", "2026-04-01T08:00:00Z"),
        ("2026-03", "x-999", "March X Post", "x", "2026-03-28T09:00:00Z"),
    ]
    for month, slug, title, source, created_at in fixtures:
        _write_bundle(
            content_dir,
            month,
            slug,
            {
                "title": title,
                "source_type": source,
                "source_url": f"https://example.com/{slug}",
                "created_at": created_at,
            },
            f"https://guchengwei.github.io/link-vault/d/{slug}/",
        )

    records = _payload(build_homepage_index(content_dir=content_dir, site_dir=site_dir).read_text(encoding="utf-8"))

    assert len(records) == 3
    assert [record["title"] for record in records] == ["April X Post", "April Web Post", "March X Post"]
    assert {record["source"] for record in records} == {"x", "web"}


def test_homepage_deduplicates_bundles_that_publish_to_the_same_page(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    public_url = "https://guchengwei.github.io/link-vault/d/web-example/"

    _write_bundle(
        content_dir,
        "2026-04",
        "web-example",
        {
            "title": "Older capture",
            "source_type": "web",
            "source_url": "https://example.com/article",
            "created_at": "2026-04-01T00:00:00Z",
        },
        public_url,
    )
    _write_bundle(
        content_dir,
        "2026-08",
        "web-example",
        {
            "title": "Newer capture",
            "source_type": "web",
            "source_url": "https://example.com/article",
            "created_at": "2026-08-01T00:00:00Z",
        },
        public_url,
    )

    records = _payload(build_homepage_index(content_dir=content_dir, site_dir=site_dir).read_text(encoding="utf-8"))

    assert [record["title"] for record in records] == ["Newer capture"]


def test_card_contract_overrides_fallback_title_opening_and_image(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    item_dir = content_dir / "2026-04" / "web-card"
    item_dir.mkdir(parents=True)
    (item_dir / "assets").mkdir()
    (item_dir / "assets" / "cover.png").write_bytes(b"not decoded by index builder")
    document = {
        "title": "Raw page title",
        "source_type": "web",
        "source_url": "https://example.com/raw",
        "created_at": "2026-04-06T00:00:00Z",
        "card": {
            "title": "Curated card title",
            "opening": "A concise opening written for the bookmark surface.",
            "image": "assets/cover.png",
        },
    }
    (item_dir / "document.json").write_text(json.dumps(document), encoding="utf-8")
    (item_dir / "index.md").write_text("# Raw page title", encoding="utf-8")
    (item_dir / "publish.json").write_text(
        json.dumps(
            {
                "published": True,
                "public_url": "https://guchengwei.github.io/link-vault/d/web-card/",
                "target": {"site_path": "site/d/web-card/index.html"},
            }
        ),
        encoding="utf-8",
    )

    record = _payload(build_homepage_index(content_dir=content_dir, site_dir=site_dir).read_text(encoding="utf-8"))[0]

    assert record["title"] == "Curated card title"
    assert record["excerpt"] == "A concise opening written for the bookmark surface."
    assert record["image"] == "d/web-card/assets/cover.png"


def test_build_homepage_index_includes_legacy_markdown_items(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    legacy_dir = content_dir / "tweets" / "2026-03"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "i-2033437609460891883.md").write_text(
        "---\nurl: \"https://x.com/i/status/2033437609460891883\"\nsource_type: tweet\ntitle: \"@dotey\"\nauthor: \"宝玉\"\ncreated_at: \"Mon Mar 16 06:58:00 +0000 2026\"\n---\n\n# @dotey\n\nLegacy tweet body.\n",
        encoding="utf-8",
    )

    record = _payload(build_homepage_index(content_dir=content_dir, site_dir=site_dir).read_text(encoding="utf-8"))[0]

    assert record["title"] == "@dotey"
    assert record["source"] == "x"
    assert record["date"] == "2026-03-16"
    assert record["url"].startswith("d/x-")
    assert "Legacy tweet body." in record["excerpt"]


def test_homepage_defaults_to_shuffled_order_with_timeline_toggle(tmp_path):
    from linkvault.site_index import build_homepage_index

    output = build_homepage_index(content_dir=tmp_path / "content", site_dir=tmp_path / "site")
    html = output.read_text(encoding="utf-8")

    assert 'id="results-summary">0 bookmarks, shuffled' in html
    assert 'id="sort-toggle"' in html
    assert 'aria-pressed="false">Timeline</button>' in html
