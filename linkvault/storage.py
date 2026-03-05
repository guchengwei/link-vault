"""
Storage — save fetched content as organized Markdown files.

Directory structure:
  content/
    tweets/YYYY-MM/screen_name-tweetid.md
    youtube/YYYY-MM/videoid.md
    web/YYYY-MM/domain-slug.md
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .fetchers import FetchResult


def _slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:max_len]


def _extract_domain(url: str) -> str:
    m = re.match(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1).replace(".", "-") if m else "unknown"


def result_to_markdown(result: FetchResult) -> str:
    """Convert a FetchResult to Markdown with YAML frontmatter."""
    lines = ["---"]
    lines.append(f"url: \"{result.url}\"")
    lines.append(f"source_type: {result.source_type}")
    lines.append(f"title: \"{result.title}\"")
    lines.append(f"author: \"{result.author}\"")
    lines.append(f"fetched_at: \"{datetime.utcnow().isoformat()}Z\"")
    for k, v in result.metadata.items():
        if isinstance(v, (str, int, float, bool)) and v is not None:
            lines.append(f"{k}: {json.dumps(v)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {result.title or result.url}")
    lines.append("")
    if result.author:
        lines.append(f"**Author:** {result.author}")
        lines.append("")
    lines.append(result.text)

    # Append quote if tweet
    qt = result.metadata.get("quote")
    if qt:
        lines.append("")
        lines.append(f"> **Quoting @{qt.get('author', '?')}:** {qt.get('text', '')}")

    # Append article if present
    art = result.metadata.get("article")
    if art and art.get("full_text"):
        lines.append("")
        lines.append(f"## Article: {art.get('title', '')}")
        lines.append("")
        lines.append(art["full_text"])

    return "\n".join(lines)


import json


def save_result(result: FetchResult, base_dir: str = "content") -> Optional[str]:
    """Save a FetchResult as Markdown. Returns the file path or None on error."""
    if not result.ok:
        return None

    now = datetime.utcnow()
    month_dir = now.strftime("%Y-%m")

    if result.source_type == "tweet":
        m = re.match(r"https://x\.com/(\w+)/status/(\d+)", result.url)
        if m:
            filename = f"{m.group(1)}-{m.group(2)}.md"
        else:
            filename = f"{_slugify(result.title or 'tweet')}.md"
        subdir = f"tweets/{month_dir}"
    elif result.source_type == "youtube":
        m = re.search(r"[?&]v=([\w-]+)", result.url)
        vid = m.group(1) if m else _slugify(result.title or "video")
        filename = f"{vid}.md"
        subdir = f"youtube/{month_dir}"
    else:
        domain = _extract_domain(result.url)
        slug = _slugify(result.title or domain)
        filename = f"{domain}-{slug}.md"
        subdir = f"web/{month_dir}"

    out_dir = Path(base_dir) / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    md = result_to_markdown(result)
    out_path.write_text(md, encoding="utf-8")
    return str(out_path)
