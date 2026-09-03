from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


ASSET_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
SOURCE_ORDER = ["x", "web", "rss", "telegram", "wechat", "xiaohongshu", "youtube", "bilibili", "unknown"]


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
    local_url: str
    source_url: str
    source_type: str
    author_label: str
    created_at: str
    bundle_path: str
    excerpt: str = ""
    image_url: str = ""
    domain: str = ""

    @property
    def month_key(self) -> str:
        parsed = _parse_created_at(self.created_at)
        if parsed:
            return parsed.strftime("%Y-%m")
        if self.created_at and len(self.created_at) >= 7 and self.created_at[4] == "-":
            return self.created_at[:7]
        for part in Path(self.bundle_path).parts:
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
        return ""


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


def _normalize_source_type(value: str) -> str:
    normalized = (value or "unknown").strip().lower()
    return {
        "webpage": "web",
        "article": "web",
        "tweet": "x",
        "tweets": "x",
        "twitter": "x",
    }.get(normalized, normalized)


def _legacy_slug(markdown_path: Path, metadata: dict) -> str:
    url = metadata.get("url") or metadata.get("final_url") or ""
    parsed = urlparse(url)
    host = (parsed.netloc or "unknown").replace(".", "-")
    digest_source = url or str(markdown_path)
    digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:12]
    source_type = _normalize_source_type(
        metadata.get("source_type")
        or (markdown_path.parts[1] if len(markdown_path.parts) > 1 else "web")
    )
    return f"{source_type}-{digest}-{host}"


def _legacy_public_url(markdown_path: Path, metadata: dict) -> str:
    return f"https://guchengwei.github.io/link-vault/d/{_legacy_slug(markdown_path, metadata)}/"


def _author_label(document: dict) -> str:
    handle = (document.get("author_handle") or "").strip()
    author = (document.get("author") or "").strip()
    return f"@{handle}" if handle else author


def _created_sort_key(value: str) -> tuple[int, str]:
    if not value:
        return (0, "")
    parsed = _parse_created_at(value)
    return (1, parsed.isoformat() if parsed else value)


def _clean_excerpt(markdown: str, limit: int = 210) -> str:
    text = re.sub(r"```.*?```", " ", markdown or "", flags=re.DOTALL)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[#>*_`~-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _relative_site_page(site_path_value: str, slug: str) -> Path:
    if site_path_value:
        path = Path(site_path_value)
        parts = path.parts
        if "site" in parts:
            return Path(*parts[parts.index("site") + 1 :])
        if not path.is_absolute():
            return path
    return Path("d") / slug / "index.html"


def _card_image(bundle_dir: Path, page_path: Path, card: dict) -> str:
    requested = card.get("image") or card.get("diagram")
    candidates: list[Path] = []
    if requested:
        candidate = bundle_dir / str(requested)
        try:
            candidate.resolve().relative_to(bundle_dir.resolve())
        except ValueError:
            candidate = Path()
        if candidate and candidate.is_file() and candidate.suffix.lower() in ASSET_SUFFIXES:
            candidates.append(candidate)

    assets_dir = bundle_dir / "assets"
    if assets_dir.exists():
        candidates.extend(
            path
            for path in sorted(assets_dir.iterdir())
            if path.is_file() and path.suffix.lower() in ASSET_SUFFIXES and path not in candidates
        )
    if not candidates:
        return ""

    selected = candidates[0]
    try:
        bundle_relative = selected.relative_to(bundle_dir)
    except ValueError:
        return ""
    return (page_path.parent / bundle_relative).as_posix()


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
        source_url = document.get("source_url") or document.get("canonical_url") or ""
        target = publish.get("target", {})
        slug = publish_path.parent.name
        page_path = _relative_site_page(target.get("site_path") or "", slug)
        card = document.get("card") if isinstance(document.get("card"), dict) else {}
        markdown_path = publish_path.with_name("index.md")
        markdown = document.get("markdown") or (
            markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
        )

        items.append(
            PublishedItem(
                title=card.get("title") or document.get("title") or source_url or public_url or slug,
                public_url=public_url,
                local_url=page_path.parent.as_posix().rstrip("/") + "/",
                source_url=source_url,
                source_type=_normalize_source_type(document.get("source_type") or "unknown"),
                author_label=_author_label(document),
                created_at=document.get("created_at") or "",
                bundle_path=target.get("bundle_path") or str(publish_path.parent.relative_to(content_path)),
                excerpt=card.get("opening") or card.get("summary") or _clean_excerpt(markdown),
                image_url=_card_image(publish_path.parent, page_path, card),
                domain=urlparse(source_url).netloc.removeprefix("www."),
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
        metadata, markdown = legacy
        public_url = _legacy_public_url(markdown_path, metadata)
        if public_url in seen_public_urls:
            continue
        slug = _legacy_slug(markdown_path, metadata)
        source_url = metadata.get("url") or metadata.get("final_url") or ""
        items.append(
            PublishedItem(
                title=metadata.get("title") or source_url or markdown_path.stem,
                public_url=public_url,
                local_url=f"d/{slug}/",
                source_url=source_url,
                source_type=_normalize_source_type(metadata.get("source_type") or "web"),
                author_label=(metadata.get("author") or "").strip(),
                created_at=metadata.get("created_at") or metadata.get("fetched_at") or "",
                bundle_path=str(markdown_path.relative_to(content_path)),
                excerpt=_clean_excerpt(markdown),
                domain=urlparse(source_url).netloc.removeprefix("www."),
            )
        )
        seen_public_urls.add(public_url)

    items.sort(key=lambda item: (_created_sort_key(item.created_at), item.title.casefold()), reverse=True)
    return items


def _payload(items: Iterable[PublishedItem]) -> str:
    records = []
    for item in items:
        records.append(
            {
                "id": item.local_url.rstrip("/").split("/")[-1],
                "title": item.title,
                "source": item.source_type,
                "author": item.author_label,
                "date": item.created_date,
                "domain": item.domain,
                "url": item.local_url or item.public_url or item.source_url,
                "sourceUrl": item.source_url,
                "excerpt": item.excerpt,
                "image": item.image_url,
            }
        )
    return json.dumps(records, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def render_homepage_index(items: Iterable[PublishedItem], title: str = "link-vault") -> str:
    item_list = list(items)
    data = _payload(item_list)
    display_title = escape(title)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A visual archive for saved links.">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#182219">
  <title>{display_title}</title>
  <link rel="stylesheet" href="assets/home.css">
</head>
<body>
  <a class="skip-link" href="#bookmarks">Skip to bookmarks</a>
  <header class="toolbar">
    <a class="brand" href="./" aria-label="{display_title} home">
      <span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M7 3.5h10a3.5 3.5 0 0 1 3.5 3.5v10a3.5 3.5 0 0 1-3.5 3.5H7A3.5 3.5 0 0 1 3.5 17V7A3.5 3.5 0 0 1 7 3.5Z"/><path d="m7.5 16.5 9-9M7.5 10v6.5H14"/></svg></span>
      <span>link/<strong>vault</strong></span>
    </a>
    <label class="search" for="search-input">
      <svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/></svg>
      <input id="search-input" type="search" autocomplete="off" placeholder="Find a bookmark…" aria-label="Search bookmarks">
      <kbd><span class="command-key">⌘</span>K</kbd>
    </label>
    <nav class="source-filters" id="source-filters" aria-label="Filter by source"></nav>
    <div class="view-toggle" role="group" aria-label="Choose bookmark view">
      <button type="button" class="icon-button is-active" data-view="grid" aria-label="Grid view" aria-pressed="true"><svg aria-hidden="true" viewBox="0 0 24 24"><rect x="4" y="4" width="6" height="6"/><rect x="14" y="4" width="6" height="6"/><rect x="4" y="14" width="6" height="6"/><rect x="14" y="14" width="6" height="6"/></svg></button>
      <button type="button" class="icon-button" data-view="list" aria-label="List view" aria-pressed="false"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 6h14M5 12h14M5 18h14"/></svg></button>
    </div>
    <div class="total-count" id="total-count" aria-live="polite">{len(item_list)} bookmarks</div>
  </header>
  <main id="bookmarks" tabindex="-1">
    <div class="results-bar">
      <p id="results-summary">{len(item_list)} bookmarks, newest first</p>
      <button class="clear-button" id="clear-search" type="button" hidden>Clear search</button>
    </div>
    <section class="bookmark-grid" id="bookmark-grid" aria-label="Saved bookmarks"></section>
    <div class="empty-state" id="empty-state" hidden>
      <span aria-hidden="true">⌕</span>
      <h2>No bookmarks found</h2>
      <p>Try another title, author, domain, or source.</p>
      <button type="button" id="reset-filters">Show all bookmarks</button>
    </div>
  </main>
  <script>window.BOOKMARKS={data};</script>
  <script src="assets/home.js"></script>
</body>
</html>
"""


def build_homepage_index(content_dir: Path | str = "content", site_dir: Path | str = "site") -> Path:
    site_path = Path(site_dir)
    asset_target = site_path / "assets"
    asset_target.mkdir(parents=True, exist_ok=True)
    asset_source = Path(__file__).with_name("site_assets")
    for name in ("home.css", "home.js"):
        shutil.copy2(asset_source / name, asset_target / name)

    output_path = site_path / "index.html"
    output_path.write_text(
        render_homepage_index(collect_published_items(content_dir)),
        encoding="utf-8",
    )
    return output_path


def main() -> int:
    build_homepage_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
