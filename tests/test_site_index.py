import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_build_homepage_index_creates_root_listing(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"

    item_dir = content_dir / "2026-04" / "x-123-example"
    item_dir.mkdir(parents=True)
    (item_dir / "document.json").write_text(
        json.dumps(
            {
                "title": "Example Saved Post",
                "source_type": "x",
                "source_url": "https://x.com/example/status/123",
                "author_handle": "example",
                "created_at": "2026-04-05T12:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    (item_dir / "publish.json").write_text(
        json.dumps(
            {
                "published": True,
                "public_url": "https://guchengwei.github.io/link-vault/d/x-123-example/",
                "target": {
                    "site_path": "site/d/x-123-example/index.html",
                    "bundle_path": "content/2026-04/x-123-example",
                },
            }
        ),
        encoding="utf-8",
    )

    output_path = build_homepage_index(content_dir=content_dir, site_dir=site_dir)

    assert output_path == site_dir / "index.html"
    html = output_path.read_text(encoding="utf-8")
    assert "Example Saved Post" in html
    assert "https://guchengwei.github.io/link-vault/d/x-123-example/" in html
    assert "@example" in html
    assert "2026-04-05" in html


def test_render_homepage_index_groups_by_month_and_shows_counts(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"

    fixtures = [
        (
            "2026-04",
            "x-123-example",
            {
                "title": "April X Post",
                "source_type": "x",
                "source_url": "https://x.com/example/status/123",
                "author_handle": "example",
                "created_at": "2026-04-05T12:00:00Z",
            },
            "https://guchengwei.github.io/link-vault/d/x-123-example/",
        ),
        (
            "2026-04",
            "web-hello",
            {
                "title": "April Web Post",
                "source_type": "web",
                "source_url": "https://example.com/post",
                "author": "Example Author",
                "created_at": "2026-04-01T08:00:00Z",
            },
            "https://guchengwei.github.io/link-vault/d/web-hello/",
        ),
        (
            "2026-03",
            "x-999-older",
            {
                "title": "March X Post",
                "source_type": "x",
                "source_url": "https://x.com/older/status/999",
                "author_handle": "older",
                "created_at": "2026-03-28T09:00:00Z",
            },
            "https://guchengwei.github.io/link-vault/d/x-999-older/",
        ),
    ]

    for month, slug, document, public_url in fixtures:
        item_dir = content_dir / month / slug
        item_dir.mkdir(parents=True)
        (item_dir / "document.json").write_text(json.dumps(document), encoding="utf-8")
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

    html = build_homepage_index(content_dir=content_dir, site_dir=site_dir).read_text(encoding="utf-8")

    assert "3 published captures" in html
    assert 'class="section-title">2026-04' in html
    assert 'class="section-title">2026-03' in html
    assert "2 items · x: 1 · web: 1" in html
    assert "1 item · x: 1" in html


def test_build_homepage_index_includes_legacy_markdown_items(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    legacy_dir = content_dir / "web" / "2026-03"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "example-com-example-domain.md").write_text(
        "---\nurl: \"https://example.com\"\nsource_type: webpage\ntitle: \"Example Domain\"\nfetched_at: \"2026-03-08T01:51:26.315113Z\"\n---\n\n# Example Domain\n\nHello from legacy markdown.\n",
        encoding="utf-8",
    )

    html = build_homepage_index(content_dir=content_dir, site_dir=site_dir).read_text(encoding="utf-8")

    assert "Example Domain" in html
    assert "https://guchengwei.github.io/link-vault/d/web-327c3fda87ce-example-com/" in html
    assert "2026-03-08" in html
    assert "1 item · web: 1" in html


def test_build_homepage_index_normalizes_legacy_tweet_dates(tmp_path):
    from linkvault.site_index import build_homepage_index

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    legacy_dir = content_dir / "tweets" / "2026-03"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "i-2033437609460891883.md").write_text(
        "---\nurl: \"https://x.com/i/status/2033437609460891883\"\nsource_type: tweet\ntitle: \"@dotey\"\nauthor: \"宝玉\"\ncreated_at: \"Mon Mar 16 06:58:00 +0000 2026\"\n---\n\n# @dotey\n\nLegacy tweet body.\n",
        encoding="utf-8",
    )

    html = build_homepage_index(content_dir=content_dir, site_dir=site_dir).read_text(encoding="utf-8")

    assert "2026-03-16" in html
    assert 'class="section-title">2026-03' in html
    assert "Latest capture: <strong>2026-03-16</strong>" in html
    assert "Mon Mar" not in html
    assert "x · 宝玉 · 2026-03-16" in html
