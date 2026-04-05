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
