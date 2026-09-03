import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_build_site_from_content_renders_bundle_pages_and_assets(tmp_path):
    from linkvault.site_builder import build_site_from_content

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"

    item_dir = content_dir / "2026-04" / "x-123-example"
    assets_dir = item_dir / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "image-01.jpg").write_bytes(b"fake-image")

    document = {
        "title": "Example Saved Post",
        "source_type": "x",
        "source_url": "https://x.com/example/status/123",
        "author_handle": "example",
        "created_at": "2026-04-05T12:00:00Z",
        "markdown": "# Example Saved Post\n\nIntro paragraph.\n\n![](assets/image-01.jpg)\n\n```python\nprint('hi')\n```\n",
        "assets": [{"local_path": "assets/image-01.jpg"}],
    }
    publish = {
        "published": True,
        "public_url": "https://guchengwei.github.io/link-vault/d/x-123-example/",
        "target": {
            "site_path": "site/d/x-123-example/index.html",
            "bundle_path": "content/2026-04/x-123-example",
        },
    }
    (item_dir / "document.json").write_text(json.dumps(document), encoding="utf-8")
    (item_dir / "publish.json").write_text(json.dumps(publish), encoding="utf-8")
    (item_dir / "index.md").write_text(document["markdown"], encoding="utf-8")

    output_paths = build_site_from_content(content_dir=content_dir, site_dir=site_dir)

    page_path = site_dir / "d" / "x-123-example" / "index.html"
    assert page_path in output_paths
    html = page_path.read_text(encoding="utf-8")
    assert "Example Saved Post" in html
    assert "Intro paragraph." in html
    assert '<img src="assets/image-01.jpg"' in html
    assert "<code>print(&#x27;hi&#x27;)</code>" in html
    assert (site_dir / "d" / "x-123-example" / "assets" / "image-01.jpg").read_bytes() == b"fake-image"
    assert (site_dir / "index.html").exists()


def test_build_site_prefers_curated_index_markdown(tmp_path):
    from linkvault.site_builder import build_site_from_content

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    item_dir = content_dir / "2026-04" / "web-curated"
    item_dir.mkdir(parents=True)
    (item_dir / "document.json").write_text(
        json.dumps(
            {
                "title": "Curated article",
                "source_type": "web",
                "source_url": "https://example.com/curated",
                "markdown": "# Noisy capture\n\nNavigation and ads.",
            }
        ),
        encoding="utf-8",
    )
    (item_dir / "index.md").write_text("# Curated article\n\nClean article body.", encoding="utf-8")
    (item_dir / "publish.json").write_text(
        json.dumps({"published": True, "target": {"site_path": "site/d/web-curated/index.html"}}),
        encoding="utf-8",
    )

    build_site_from_content(content_dir=content_dir, site_dir=site_dir)

    html = (site_dir / "d" / "web-curated" / "index.html").read_text(encoding="utf-8")
    assert "Clean article body." in html
    assert "Navigation and ads." not in html


def test_build_site_from_content_renders_ordered_lists(tmp_path):
    from linkvault.site_builder import build_site_from_content

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"

    item_dir = content_dir / "2026-04" / "web-ordered-example"
    item_dir.mkdir(parents=True)

    document = {
        "title": "Ordered List Example",
        "source_type": "web",
        "source_url": "https://example.com/ordered",
        "created_at": "2026-04-05T12:00:00Z",
        "markdown": "# Ordered List Example\n\n参考资料\n\n1. 第一条\n2. 第二条\n3. 第三条\n",
    }
    publish = {
        "published": True,
        "public_url": "https://guchengwei.github.io/link-vault/d/web-ordered-example/",
        "target": {
            "site_path": "site/d/web-ordered-example/index.html",
            "bundle_path": "content/2026-04/web-ordered-example",
        },
    }
    (item_dir / "document.json").write_text(json.dumps(document), encoding="utf-8")
    (item_dir / "publish.json").write_text(json.dumps(publish), encoding="utf-8")
    (item_dir / "index.md").write_text(document["markdown"], encoding="utf-8")

    build_site_from_content(content_dir=content_dir, site_dir=site_dir)

    html = (site_dir / "d" / "web-ordered-example" / "index.html").read_text(encoding="utf-8")
    assert "<ol><li>第一条</li><li>第二条</li><li>第三条</li></ol>" in html


def test_build_site_honors_custom_output_directory(tmp_path):
    from linkvault.site_builder import build_site_from_content

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "dist"
    item_dir = content_dir / "2026-04" / "web-custom-output"
    item_dir.mkdir(parents=True)
    document = {
        "title": "Custom output",
        "source_type": "web",
        "source_url": "https://example.com/custom",
        "markdown": "Custom output body.",
    }
    publish = {
        "published": True,
        "public_url": "https://example.com/d/web-custom-output/",
        "target": {"site_path": "site/d/web-custom-output/index.html"},
    }
    (item_dir / "document.json").write_text(json.dumps(document), encoding="utf-8")
    (item_dir / "publish.json").write_text(json.dumps(publish), encoding="utf-8")

    build_site_from_content(content_dir=content_dir, site_dir=site_dir)

    assert (site_dir / "d" / "web-custom-output" / "index.html").is_file()


def test_build_site_from_content_renders_legacy_markdown_files(tmp_path):
    from linkvault.site_builder import build_site_from_content

    content_dir = tmp_path / "content"
    site_dir = tmp_path / "site"
    legacy_dir = content_dir / "web" / "2026-03"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "example-com-example-domain.md").write_text(
        "---\nurl: \"https://example.com\"\nsource_type: webpage\ntitle: \"Example Domain\"\nauthor: \"\"\n---\n\n# Example Domain\n\nHello from markdown.\n",
        encoding="utf-8",
    )

    output_paths = build_site_from_content(content_dir=content_dir, site_dir=site_dir)

    page_path = site_dir / "d" / "web-327c3fda87ce-example-com" / "index.html"
    assert page_path in output_paths
    html = page_path.read_text(encoding="utf-8")
    assert "Example Domain" in html
    assert "Hello from markdown." in html
    assert "https://example.com" in html
