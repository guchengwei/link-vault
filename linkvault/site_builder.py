from __future__ import annotations

import hashlib
import json
import re
import shutil
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from .site_index import build_homepage_index


_CODE_FENCE_RE = re.compile(r"^```(?P<lang>[\w+-]*)\s*$")
_IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")
_LINK_RE = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<href>[^)]+)\)")
_ORDERED_LIST_RE = re.compile(r"^\d+\.\s+(?P<item>.+)$")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _inline_html(text: str) -> str:
    escaped = escape(text)
    escaped = _LINK_RE.sub(lambda m: f'<a href="{escape(m.group("href"), quote=True)}">{escape(m.group("label"))}</a>', escaped)
    escaped = _IMAGE_RE.sub(lambda m: f'<img src="{escape(m.group("src"), quote=True)}" alt="{escape(m.group("alt"))}" loading="lazy">', escaped)
    return escaped


def _normalize_source_prefix(value: str) -> str:
    value = (value or "web").strip().lower()
    return {
        "webpage": "web",
        "article": "web",
        "tweet": "x",
        "tweets": "x",
        "twitter": "x",
    }.get(value, value)


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


def _legacy_site_path(markdown_path: Path, metadata: dict, site_root: Path) -> tuple[Path, str]:
    url = metadata.get("url") or metadata.get("final_url") or ""
    parsed = urlparse(url)
    host = (parsed.netloc or "unknown").replace(".", "-")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12] if url else hashlib.sha1(str(markdown_path).encode("utf-8")).hexdigest()[:12]
    prefix = _normalize_source_prefix(metadata.get("source_type") or markdown_path.parts[1] if len(markdown_path.parts) > 1 else "web")
    slug = f"{prefix}-{digest}-{host}"
    return site_root / "d" / slug / "index.html", slug


def _published_site_path(site_root: Path, site_path_value: str, slug: str) -> Path:
    if not site_path_value:
        return site_root / "d" / slug / "index.html"

    configured = Path(site_path_value)
    if configured.is_absolute():
        return configured
    if configured.parts and configured.parts[0] == "site":
        configured = Path(*configured.parts[1:])
    return site_root / configured


def render_markdown_html(markdown: str) -> str:
    lines = markdown.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    code_lines: list[str] = []
    code_lang = ""
    in_code = False
    list_items: list[str] = []
    list_kind: str | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(part.strip() for part in paragraph if part.strip())
            blocks.append(f"<p>{_inline_html(text)}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items, list_kind
        if list_items:
            items = "".join(f"<li>{_inline_html(item)}</li>" for item in list_items)
            tag = "ol" if list_kind == "ol" else "ul"
            blocks.append(f"<{tag}>{items}</{tag}>")
            list_items = []
            list_kind = None

    def flush_code() -> None:
        nonlocal code_lines, code_lang
        blocks.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
        code_lines = []
        code_lang = ""

    for raw_line in lines:
        line = raw_line.rstrip()
        fence = _CODE_FENCE_RE.match(line)
        if fence:
            flush_paragraph()
            flush_list()
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
                code_lang = fence.group("lang")
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        if line.startswith("# "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h1>{_inline_html(line[2:].strip())}</h1>")
            continue
        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h2>{_inline_html(line[3:].strip())}</h2>")
            continue
        if line.startswith("### "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h3>{_inline_html(line[4:].strip())}</h3>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            if list_kind not in (None, "ul"):
                flush_list()
            list_kind = "ul"
            list_items.append(line[2:].strip())
            continue
        ordered_match = _ORDERED_LIST_RE.match(line)
        if ordered_match:
            flush_paragraph()
            if list_kind not in (None, "ol"):
                flush_list()
            list_kind = "ol"
            list_items.append(ordered_match.group("item").strip())
            continue
        if _IMAGE_RE.fullmatch(line.strip()):
            flush_paragraph()
            flush_list()
            blocks.append(_inline_html(line.strip()))
            continue

        paragraph.append(line)

    flush_paragraph()
    flush_list()
    if in_code:
        flush_code()
    return "\n".join(blocks)


def _render_page(document: dict, public_url: str, body_html: str) -> str:
    title = document.get("title") or public_url
    source_url = document.get("source_url") or document.get("canonical_url") or ""
    author = document.get("author_handle") or document.get("author") or ""
    created_at = document.get("created_at") or ""
    meta_parts = [escape(document.get("source_type") or "unknown")]
    if author:
        meta_parts.append(escape(f"@{author}" if document.get("author_handle") else author))
    if created_at:
        meta_parts.append(escape(created_at[:10]))
    if source_url:
        meta_parts.append(f'<a href="{escape(source_url, quote=True)}">source</a>')
    meta_html = " · ".join(meta_parts)
    canonical = f'<link rel="canonical" href="{escape(public_url, quote=True)}">' if public_url else ""
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escape(title)}</title>
  {canonical}
  <style>
    :root {{ color-scheme: dark; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", "Noto Sans JP", sans-serif; margin: 0; background: #182219; color: #272017; }}
    main {{ max-width: 900px; margin: 0 auto; padding: 2rem 1rem 5rem; }}
    .shell {{ background: #f0e7d4; border: 1px solid rgba(214, 166, 58, .6); border-radius: 14px; padding: clamp(1.25rem, 4vw, 3.25rem); box-shadow: 0 18px 48px rgba(5, 12, 6, .28); }}
    .back {{ display: inline-flex; margin-bottom: 1.5rem; color: #2f716b; font-weight: 700; text-decoration: none; }}
    .back:hover {{ text-decoration: underline; }}
    h1 {{ margin: 0 0 0.65rem; font-family: Georgia, "Noto Serif CJK SC", "Noto Serif JP", ui-serif, serif; font-size: clamp(2rem, 5vw, 3.4rem); line-height: 1.12; letter-spacing: -.025em; }}
    .meta {{ color: #675c4c; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(77, 58, 32, .18); }}
    .meta a {{ color: #2f716b; }}
    article {{ line-height: 1.75; font-size: 1.05rem; }}
    article h2, article h3 {{ font-family: Georgia, "Noto Serif CJK SC", "Noto Serif JP", ui-serif, serif; line-height: 1.25; }}
    article img {{ max-width: 100%; height: auto; border-radius: 10px; display: block; margin: 1.5rem auto; border: 1px solid rgba(77, 58, 32, .16); }}
    article pre {{ overflow-x: auto; padding: 1rem; border-radius: 10px; background: #202a20; color: #fff7e5; }}
    article code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    article p, article ul {{ margin: 0 0 1rem; }}
    article a {{ color: #2f716b; }}
  </style>
</head>
<body>
  <main>
    <div class=\"shell\">
      <a class=\"back\" href=\"../../\">← link-vault</a>
      <h1>{escape(title)}</h1>
      <div class=\"meta\">{meta_html}</div>
      <article>
        {body_html}
      </article>
    </div>
  </main>
</body>
</html>
"""


def build_site_from_content(content_dir: Path | str = "content", site_dir: Path | str = "site") -> list[Path]:
    content_root = Path(content_dir)
    site_root = Path(site_dir)
    output_paths: list[Path] = []
    rendered_pages: set[Path] = set()

    for publish_path in sorted(content_root.glob("**/publish.json")):
        publish = _load_json(publish_path)
        if not publish.get("published"):
            continue
        document_path = publish_path.with_name("document.json")
        if not document_path.exists():
            continue
        document = _load_json(document_path)
        markdown = document.get("markdown") or publish_path.with_name("index.md").read_text(encoding="utf-8")

        site_path_value = publish.get("target", {}).get("site_path") or ""
        site_page = _published_site_path(site_root, site_path_value, publish_path.parent.name)
        site_page.parent.mkdir(parents=True, exist_ok=True)

        bundle_dir = publish_path.parent
        asset_source = bundle_dir / "assets"
        asset_target = site_page.parent / "assets"
        if asset_source.exists():
            shutil.copytree(asset_source, asset_target, dirs_exist_ok=True)

        body_html = render_markdown_html(markdown)
        page_html = _render_page(document, publish.get("public_url") or "", body_html)
        site_page.write_text(page_html, encoding="utf-8")
        output_paths.append(site_page)
        rendered_pages.add(site_page)

    for markdown_path in sorted(content_root.glob("**/*.md")):
        if markdown_path.name == "index.md":
            continue
        legacy = _parse_legacy_markdown(markdown_path)
        if not legacy:
            continue
        metadata, markdown = legacy
        site_page, slug = _legacy_site_path(markdown_path, metadata, site_root)
        if site_page in rendered_pages:
            continue
        site_page.parent.mkdir(parents=True, exist_ok=True)
        public_url = f"https://guchengwei.github.io/link-vault/d/{slug}/"
        document = {
            "title": metadata.get("title") or metadata.get("url") or slug,
            "source_type": _normalize_source_prefix(metadata.get("source_type") or markdown_path.parts[1] if len(markdown_path.parts) > 1 else "web"),
            "source_url": metadata.get("url") or metadata.get("final_url") or "",
            "author": metadata.get("author") or "",
            "created_at": metadata.get("created_at") or metadata.get("fetched_at") or "",
        }
        body_html = render_markdown_html(markdown)
        page_html = _render_page(document, public_url, body_html)
        site_page.write_text(page_html, encoding="utf-8")
        output_paths.append(site_page)
        rendered_pages.add(site_page)

    output_paths.append(build_homepage_index(content_dir=content_root, site_dir=site_root))
    return output_paths


def main() -> int:
    build_site_from_content()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
