"""
Content fetchers — source-specific adapters for URL content extraction.

Adapters:
  - X/Twitter: via vendored x-tweet-fetcher (FxTwitter API)
  - YouTube: transcript via yt-dlp
  - Generic web: readability + BeautifulSoup fallback
"""

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path

# ---------------------------------------------------------------------------
# Result dataclass — stable output shape for all adapters
# ---------------------------------------------------------------------------

@dataclass
class FetchResult:
    ok: bool
    url: str
    source_type: str  # "tweet", "youtube", "webpage"
    title: str = ""
    author: str = ""
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

# ---------------------------------------------------------------------------
# URL classification
# ---------------------------------------------------------------------------

_TWEET_RE = re.compile(
    r"https?://(?:www\.)?(?:x\.com|twitter\.com)/(\w+)/status/(\d+)", re.I
)
_YT_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)", re.I
)


def classify_url(url: str) -> str:
    if _TWEET_RE.match(url):
        return "tweet"
    if _YT_RE.match(url):
        return "youtube"
    return "webpage"

# ---------------------------------------------------------------------------
# Tweet fetcher (via FxTwitter API — zero deps)
# ---------------------------------------------------------------------------

def fetch_tweet(url: str, timeout: int = 15, retries: int = 2) -> FetchResult:
    m = _TWEET_RE.match(url)
    if not m:
        return FetchResult(ok=False, url=url, source_type="tweet",
                           error=f"Not a valid tweet URL: {url}")
    username, tweet_id = m.group(1), m.group(2)
    canonical = f"https://x.com/{username}/status/{tweet_id}"
    api_url = f"https://api.fxtwitter.com/{username}/status/{tweet_id}"

    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            if data.get("code") != 200:
                return FetchResult(ok=False, url=canonical, source_type="tweet",
                                   error=f"FxTwitter {data.get('code')}: {data.get('message')}")
            tw = data["tweet"]
            meta = {
                "likes": tw.get("likes", 0),
                "retweets": tw.get("retweets", 0),
                "views": tw.get("views"),
                "replies_count": tw.get("replies", 0),
                "bookmarks": tw.get("bookmarks", 0),
                "created_at": tw.get("created_at", ""),
                "lang": tw.get("lang", ""),
                "is_note_tweet": tw.get("is_note_tweet", False),
            }
            # Media
            media_all = tw.get("media", {})
            if media_all and media_all.get("all"):
                meta["media"] = [{"type": m.get("type"), "url": m.get("url")}
                                 for m in media_all["all"]]
            # Quote
            qt = tw.get("quote")
            if qt:
                meta["quote"] = {
                    "text": qt.get("text", ""),
                    "author": qt.get("author", {}).get("screen_name", ""),
                    "url": qt.get("url", ""),
                }
            # Article
            article = tw.get("article")
            if article:
                blocks = article.get("content", {}).get("blocks", [])
                full = "\n\n".join(b.get("text", "") for b in blocks if b.get("text"))
                meta["article"] = {
                    "title": article.get("title", ""),
                    "full_text": full,
                    "word_count": len(full.split()) if full else 0,
                }
            return FetchResult(
                ok=True, url=canonical, source_type="tweet",
                title=f"@{tw.get('author', {}).get('screen_name', username)}",
                author=tw.get("author", {}).get("name", username),
                text=tw.get("text", ""),
                metadata=meta,
            )
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last_err = str(e)
            if attempt < retries - 1:
                time.sleep(1 * (2 ** attempt))
    return FetchResult(ok=False, url=canonical, source_type="tweet",
                       error=f"Network error after {retries} attempts: {last_err}")

# ---------------------------------------------------------------------------
# YouTube fetcher (transcript via yt-dlp)
# ---------------------------------------------------------------------------

def fetch_youtube(url: str, timeout: int = 30) -> FetchResult:
    m = _YT_RE.match(url)
    video_id = m.group(1) if m else ""
    canonical = f"https://www.youtube.com/watch?v={video_id}" if video_id else url

    # Get metadata
    try:
        proc = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", "--no-playlist", url],
            capture_output=True, text=True, timeout=timeout,
        )
        if proc.returncode != 0:
            return FetchResult(ok=False, url=canonical, source_type="youtube",
                               error=f"yt-dlp metadata failed: {proc.stderr[:300]}")
        info = json.loads(proc.stdout)
    except FileNotFoundError:
        return FetchResult(ok=False, url=canonical, source_type="youtube",
                           error="yt-dlp not installed")
    except subprocess.TimeoutExpired:
        return FetchResult(ok=False, url=canonical, source_type="youtube",
                           error="yt-dlp timed out")

    title = info.get("title", "")
    author = info.get("uploader", info.get("channel", ""))
    description = info.get("description", "")

    # Try to get subtitles/transcript
    transcript = ""
    try:
        proc2 = subprocess.run(
            ["yt-dlp", "--write-auto-sub", "--sub-lang", "en,zh,ja,ko",
             "--skip-download", "--sub-format", "vtt",
             "--print", "%(requested_subtitles)j", url],
            capture_output=True, text=True, timeout=timeout,
        )
        # Fallback: get subtitles to a temp file
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["yt-dlp", "--write-auto-sub", "--sub-lang", "en,zh,ja,ko",
                 "--skip-download", "--sub-format", "vtt",
                 "-o", f"{tmpdir}/sub", url],
                capture_output=True, text=True, timeout=timeout,
            )
            # Find any .vtt file
            for f in Path(tmpdir).glob("*.vtt"):
                raw = f.read_text(errors="replace")
                # Strip VTT headers and timestamps
                lines = []
                for line in raw.splitlines():
                    if re.match(r"^\d{2}:\d{2}:", line) or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:") or not line.strip():
                        continue
                    # Strip inline timestamps
                    clean = re.sub(r"<\d{2}:\d{2}:[\d.]+>", "", line).strip()
                    if clean and (not lines or lines[-1] != clean):
                        lines.append(clean)
                transcript = "\n".join(lines)
                break
    except Exception:
        pass  # transcript is optional

    text_parts = []
    if description:
        text_parts.append(description)
    if transcript:
        text_parts.append(f"\n--- Transcript ---\n{transcript}")

    meta = {
        "duration": info.get("duration"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "upload_date": info.get("upload_date", ""),
        "channel_id": info.get("channel_id", ""),
        "has_transcript": bool(transcript),
    }

    return FetchResult(
        ok=True, url=canonical, source_type="youtube",
        title=title, author=author,
        text="\n\n".join(text_parts),
        metadata=meta,
    )

# ---------------------------------------------------------------------------
# Generic webpage fetcher (readability + bs4)
# ---------------------------------------------------------------------------

def fetch_webpage(url: str, timeout: int = 15) -> FetchResult:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; LinkVault/0.1)",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode(errors="replace")
            final_url = resp.url
    except Exception as e:
        return FetchResult(ok=False, url=url, source_type="webpage",
                           error=f"Fetch failed: {e}")

    title = ""
    text = ""

    # Try readability first
    try:
        from readability import Document
        doc = Document(html)
        title = doc.title()
        summary_html = doc.summary()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(summary_html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
    except Exception:
        # Fallback: raw BeautifulSoup
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            title = soup.title.string if soup.title else ""
            text = soup.get_text(separator="\n", strip=True)
            # Collapse blank lines
            text = re.sub(r"\n{3,}", "\n\n", text)
        except Exception as e2:
            return FetchResult(ok=False, url=url, source_type="webpage",
                               error=f"Parse failed: {e2}")

    meta = {"final_url": final_url}
    return FetchResult(
        ok=True, url=url, source_type="webpage",
        title=title or "", author="", text=text,
        metadata=meta,
    )

# ---------------------------------------------------------------------------
# Router — pick the right adapter
# ---------------------------------------------------------------------------

def fetch(url: str, **kwargs) -> FetchResult:
    """Fetch content from any supported URL."""
    source = classify_url(url)
    if source == "tweet":
        return fetch_tweet(url, **{k: v for k, v in kwargs.items() if k in ("timeout", "retries")})
    elif source == "youtube":
        return fetch_youtube(url, **{k: v for k, v in kwargs.items() if k in ("timeout",)})
    else:
        return fetch_webpage(url, **{k: v for k, v in kwargs.items() if k in ("timeout",)})


def fetch_batch(urls: List[str], **kwargs) -> List[FetchResult]:
    """Fetch multiple URLs."""
    return [fetch(url, **kwargs) for url in urls]
