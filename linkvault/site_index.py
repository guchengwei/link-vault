from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


def _parse_created_at(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


@dataclass
class PublishedItem:
    title: str
    public_url: str
    source_url: str
    source_type: str
    author_label: str
    created_at: str
    bundle_path: str

    @property
    def month_key(self) -> str:
        parsed = _parse_created_at(self.created_at)
        if parsed:
            return parsed.strftime("%Y-%m")
        if self.created_at and len(self.created_at) >= 7 and self.created_at[4] == "-":
            return self.created_at[:7]
        parts = Path(self.bundle_path).parts
        for part in parts:
            if len(part) == 7 and part[4] == "-":
                return part
        return "unknown"

    @property
    def created_date(self) -> str:
        parsed = _parse_created_at(self.created_at)
        if parsed:
            return parsed.strftime("%Y-%m-%d")
        if self.created_at and len(self.created_at) >= 10 and self.created_at[4] == "-":
            return self.created_at[:10]
        return "unknown"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_legacy_markdown(path: Path) -> tuple[dict, str] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    try:
        _, frontmatter, markdown = text.split("---\n", 2)
    except ValueError:
        return None

    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, markdown.strip()


def _legacy_public_url(markdown_path: Path, metadata: dict) -> str:
    url = metadata.get("url") or metadata.get("final_url") or ""
    parsed = urlparse(url)
    host = (parsed.netloc or "unknown").replace(".", "-")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12] if url else hashlib.sha1(str(markdown_path).encode("utf-8")).hexdigest()[:12]
    source_type = _normalize_source_type((metadata.get("source_type") or markdown_path.parts[1] if len(markdown_path.parts) > 1 else "web"))
    prefix = source_type
    slug = f"{prefix}-{digest}-{host}"
    return f"https://guchengwei.github.io/link-vault/d/{slug}/"


def _author_label(document: dict) -> str:
    handle = (document.get("author_handle") or "").strip()
    author = (document.get("author") or "").strip()
    if handle:
        return f"@{handle}"
    return author


def _created_sort_key(value: str) -> tuple[int, str]:
    if not value:
        return (0, "")
    parsed = _parse_created_at(value)
    if parsed:
        return (1, parsed.isoformat())
    return (1, value)


def _month_sort_key(value: str) -> tuple[int, str]:
    if not value or value == "unknown":
        return (0, "")
    return (1, value)


SOURCE_ORDER = ["x", "web", "rss", "telegram", "wechat", "xiaohongshu", "youtube", "bilibili", "unknown"]


def _normalize_source_type(value: str) -> str:
    normalized = (value or "unknown").strip().lower()
    return {
        "webpage": "web",
        "article": "web",
        "tweet": "x",
        "tweets": "x",
        "twitter": "x",
    }.get(normalized, normalized)


def _format_count(value: int) -> str:
    return "1 item" if value == 1 else f"{value} items"


def _source_sort_key(source: str) -> tuple[int, str]:
    try:
        return (0, SOURCE_ORDER.index(source))
    except ValueError:
        return (1, source)


def _render_item(item: PublishedItem) -> str:
    meta_parts = [escape(item.source_type)]
    if item.author_label:
        meta_parts.append(escape(item.author_label))
    if item.created_at:
        meta_parts.append(escape(item.created_date))
    if item.source_url:
        meta_parts.append(f'<a href="{escape(item.source_url, quote=True)}">source</a>')
    meta = " · ".join(meta_parts)
    return (
        '<article class="card">'
        f'<a class="card-title" href="{escape(item.public_url, quote=True)}">{escape(item.title)}</a>'
        f'<div class="meta">{meta}</div>'
        '</article>'
    )


def collect_published_items(content_dir: Path | str) -> list[PublishedItem]:
    content_path = Path(content_dir)
    items: list[PublishedItem] = []
    seen_public_urls: set[str] = set()

    for publish_path in content_path.glob("**/publish.json"):
        publish = _load_json(publish_path)
        if not publish.get("published"):
            continue

        document_path = publish_path.with_name("document.json")
        if not document_path.exists():
            continue
        document = _load_json(document_path)
        public_url = publish.get("public_url") or ""

        items.append(
            PublishedItem(
                title=document.get("title") or document.get("source_url") or public_url or publish_path.parent.name,
                public_url=public_url,
                source_url=document.get("source_url") or document.get("canonical_url") or "",
                source_type=_normalize_source_type(document.get("source_type") or "unknown"),
                author_label=_author_label(document),
                created_at=document.get("created_at") or "",
                bundle_path=publish.get("target", {}).get("bundle_path") or str(publish_path.parent.relative_to(content_path)),
            )
        )
        if public_url:
            seen_public_urls.add(public_url)

    for markdown_path in content_path.glob("**/*.md"):
        if markdown_path.name == "index.md":
            continue
        legacy = _parse_legacy_markdown(markdown_path)
        if not legacy:
            continue
        metadata, _markdown = legacy
        public_url = _legacy_public_url(markdown_path, metadata)
        if public_url in seen_public_urls:
            continue
        items.append(
            PublishedItem(
                title=metadata.get("title") or metadata.get("url") or markdown_path.stem,
                public_url=public_url,
                source_url=metadata.get("url") or metadata.get("final_url") or "",
                source_type=_normalize_source_type(metadata.get("source_type") or "web"),
                author_label=(metadata.get("author") or "").strip(),
                created_at=metadata.get("created_at") or metadata.get("fetched_at") or "",
                bundle_path=str(markdown_path.relative_to(content_path)),
            )
        )
        seen_public_urls.add(public_url)

    items.sort(key=lambda item: (_created_sort_key(item.created_at), item.title.casefold()), reverse=True)
    return items


def render_homepage_index(items: Iterable[PublishedItem], title: str = "link-vault") -> str:
    item_list = list(items)
    total = len(item_list)
    latest = item_list[0].created_date if item_list else None

    grouped: dict[str, list[PublishedItem]] = {}
    for item in item_list:
        grouped.setdefault(item.month_key, []).append(item)

    sections = []
    for month in sorted(grouped.keys(), key=_month_sort_key, reverse=True):
        month_items = grouped[month]
        source_counts = Counter(item.source_type for item in month_items)
        count_summary = [
            _format_count(len(month_items)),
            *[f"{source}: {source_counts[source]}" for source in sorted(source_counts, key=_source_sort_key)],
        ]
        cards = "\n".join(_render_item(item) for item in month_items)
        sections.append(
            '<section class="month-section">'
            '<div class="section-head">'
            f'<h2 class="section-title">{escape(month)}</h2>'
            f'<div class="section-meta">{" · ".join(count_summary)}</div>'
            '</div>'
            f'<div class="card-list">{cards}</div>'
            '</section>'
        )

    section_markup = "\n".join(sections) if sections else '<div class="empty">No published items yet.</div>'
    latest_line = f'Latest capture: <strong>{escape(latest)}</strong>' if latest else 'No captures published yet.'

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escape(title)}</title>
  <style>
    :root {{ color-scheme: light dark; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; background: #f5f5f7; color: #111; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 2rem 1rem 4rem; }}
    .hero {{ background: #fff; border: 1px solid #ddd; border-radius: 16px; padding: 1.25rem 1.25rem 1rem; margin-bottom: 1rem; }}
    h1 {{ margin: 0 0 0.35rem; font-size: 2rem; }}
    .subtitle {{ color: #666; margin: 0 0 1rem; }}
    .stats {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 0; padding: 0; list-style: none; }}
    .stats li {{ background: #f2f2f2; border-radius: 999px; padding: 0.4rem 0.7rem; font-size: 0.95rem; }}
    .month-section {{ margin-top: 1.25rem; }}
    .section-head {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.5rem; align-items: baseline; margin-bottom: 0.75rem; }}
    .section-title {{ margin: 0; font-size: 1.1rem; }}
    .section-meta {{ color: #666; font-size: 0.95rem; }}
    .card-list {{ display: grid; gap: 0.75rem; }}
    .card {{ background: #fff; border: 1px solid #ddd; border-radius: 14px; padding: 0.9rem 1rem; }}
    .card-title {{ color: inherit; display: inline-block; font-weight: 600; text-decoration: none; }}
    .card-title:hover {{ text-decoration: underline; }}
    .meta {{ color: #666; font-size: 0.95rem; margin-top: 0.3rem; }}
    .meta a {{ color: inherit; }}
    .empty {{ color: #666; background: #fff; border: 1px solid #ddd; border-radius: 14px; padding: 1rem; }}
    @media (prefers-color-scheme: dark) {{
      body {{ background: #111214; color: #f5f5f7; }}
      .hero, .card, .empty {{ background: #18191c; border-color: #34363b; }}
      .subtitle, .section-meta, .meta {{ color: #a7acb5; }}
      .stats li {{ background: #22242a; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class=\"hero\">
      <h1>{escape(title)}</h1>
      <p class=\"subtitle\">Published captures from xfetch.</p>
      <ul class=\"stats\">
        <li>{total} published captures</li>
        <li>{latest_line}</li>
      </ul>
    </section>
    {section_markup}
  </main>
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
