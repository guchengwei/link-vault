from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Iterable


@dataclass
class PublishedItem:
    title: str
    public_url: str
    source_url: str
    source_type: str
    author_label: str
    created_at: str
    bundle_path: str


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _author_label(document: dict) -> str:
    handle = (document.get("author_handle") or "").strip()
    author = (document.get("author") or "").strip()
    if handle:
        return f"@{handle}"
    return author


def _created_sort_key(value: str) -> tuple[int, str]:
    if not value:
        return (0, "")
    normalized = value.replace("Z", "+00:00")
    try:
        return (1, datetime.fromisoformat(normalized).isoformat())
    except ValueError:
        return (1, value)


def collect_published_items(content_dir: Path | str) -> list[PublishedItem]:
    content_path = Path(content_dir)
    items: list[PublishedItem] = []

    for publish_path in content_path.glob("**/publish.json"):
        publish = _load_json(publish_path)
        if not publish.get("published"):
            continue

        document_path = publish_path.with_name("document.json")
        if not document_path.exists():
            continue
        document = _load_json(document_path)

        items.append(
            PublishedItem(
                title=document.get("title") or document.get("source_url") or publish.get("public_url") or publish_path.parent.name,
                public_url=publish.get("public_url") or "",
                source_url=document.get("source_url") or document.get("canonical_url") or "",
                source_type=document.get("source_type") or "unknown",
                author_label=_author_label(document),
                created_at=document.get("created_at") or "",
                bundle_path=publish.get("target", {}).get("bundle_path") or str(publish_path.parent.relative_to(content_path)),
            )
        )

    items.sort(key=lambda item: (_created_sort_key(item.created_at), item.title.casefold()), reverse=True)
    return items


def render_homepage_index(items: Iterable[PublishedItem], title: str = "link-vault") -> str:
    item_list = list(items)
    rows = []
    for item in item_list:
        meta_parts = [escape(item.source_type)]
        if item.author_label:
            meta_parts.append(escape(item.author_label))
        if item.created_at:
            meta_parts.append(escape(item.created_at[:10]))
        if item.source_url:
            meta_parts.append(f'<a href="{escape(item.source_url, quote=True)}">source</a>')
        meta = " · ".join(meta_parts)
        rows.append(
            "<li>"
            f'<a href="{escape(item.public_url, quote=True)}">{escape(item.title)}</a>'
            f'<div class="meta">{meta}</div>'
            "</li>"
        )

    if rows:
        list_markup = "\n".join(rows)
    else:
        list_markup = '<li><div class="meta">No published items yet.</div></li>'

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escape(title)}</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem auto; max-width: 860px; padding: 0 1rem; line-height: 1.5; }}
    h1 {{ margin-bottom: 0.25rem; }}
    p {{ color: #666; margin-top: 0; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ border-top: 1px solid #ddd; padding: 0.9rem 0; }}
    li:last-child {{ border-bottom: 1px solid #ddd; }}
    a {{ text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .meta {{ color: #666; font-size: 0.95rem; margin-top: 0.2rem; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <p>Published captures from xfetch.</p>
  <ul>
    {list_markup}
  </ul>
</body>
</html>
"""


def build_homepage_index(content_dir: Path | str = "content", site_dir: Path | str = "site") -> Path:
    site_path = Path(site_dir)
    site_path.mkdir(parents=True, exist_ok=True)
    output_path = site_path / "index.html"
    html = render_homepage_index(collect_published_items(content_dir))
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> int:
    build_homepage_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
