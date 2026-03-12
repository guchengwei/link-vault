"""
Content fetchers — general-purpose link processor.

Strategy:
  1. Camofox (browser automation) is the PRIMARY fetcher for ALL URLs.
     It renders any page in a real browser and returns the accessibility
     tree snapshot — works for Reddit, X/Twitter, paywalled sites, SPAs, etc.
  2. Source-specific enrichments are layered on top:
     - X/Twitter: also fetch structured data via FxTwitter API (stats, media)
     - YouTube: also fetch metadata + transcript via yt-dlp
  3. Fallbacks when Camofox is unavailable:
     - X/Twitter: FxTwitter API only
     - YouTube: yt-dlp only
     - Everything else: readability + BeautifulSoup

Adapters:
  - Camofox (any URL)         — primary, via x-tweet-fetcher's camofox_client
  - X/Twitter enrichment      — FxTwitter API for structured stats/media
  - YouTube enrichment        — yt-dlp for metadata + transcript
  - readability + bs4         — fallback for generic web when Camofox down
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
# Camofox client — import from vendored x-tweet-fetcher
# ---------------------------------------------------------------------------

_VENDOR_DIR = Path(__file__).resolve().parent.parent.parent / "vendor" / "x-tweet-fetcher" / "scripts"
sys.path.insert(0, str(_VENDOR_DIR))

try:
    from camofox_client import check_camofox, camofox_fetch_page
    _HAS_CAMOFOX_CLIENT = True
except ImportError:
    _HAS_CAMOFOX_CLIENT = False

# ---------------------------------------------------------------------------
# Result dataclass — stable output shape for all adapters
# ---------------------------------------------------------------------------

@dataclass
class FetchResult:
    ok: bool
    url: str
    source_type: str  # "tweet", "youtube", "webpage", "reddit", etc.
    title: str = ""
    author: str = ""
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

# ---------------------------------------------------------------------------
# URL classification (for enrichment routing, not gating)
# ---------------------------------------------------------------------------

_TWEET_RE = re.compile(
    r"https?://(?:www\.)?(?:x\.com|twitter\.com)/(\w+)/status/(\d+)", re.I
)
_YT_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)", re.I
)
_REDDIT_RE = re.compile(
    r"https?://(?:www\.)?(?:old\.)?reddit\.com/r/\w+", re.I
)
_BILIBILI_RE = re.compile(
    r"https?://(?:www\.)?bilibili\.com/video/([A-Za-z0-9]+)", re.I
)


def classify_url(url: str) -> str:
    """Classify URL for enrichment purposes. Every URL is fetchable."""
    if _TWEET_RE.match(url):
        return "tweet"
    if _YT_RE.match(url):
        return "youtube"
    if _REDDIT_RE.match(url):
        return "reddit"
    if _BILIBILI_RE.match(url):
        return "bilibili"
    return "webpage"

# ---------------------------------------------------------------------------
# Camofox: primary fetcher for ANY URL
# ---------------------------------------------------------------------------

def _camofox_available(port: int = 9377) -> bool:
    if not _HAS_CAMOFOX_CLIENT:
        return False
    return check_camofox(port)


def _parse_snapshot_to_text(snapshot: str) -> tuple:
    """Extract title and clean text from Camofox accessibility tree snapshot."""
    if not snapshot:
        return "", ""

    lines = snapshot.strip().splitlines()
    title = ""
    text_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Extract title from first heading
        heading_m = re.search(r'heading "(.+?)"', stripped)
        if heading_m and not title:
            title = heading_m.group(1)

        # Extract text content from various snapshot patterns
        for pattern in [
            r'^- text:\s*(.+)',
            r'^text:\s*(.+)',
            r'^- paragraph:\s*(.+)',
            r'^paragraph:\s*(.+)',
        ]:
            m = re.match(pattern, stripped)
            if m:
                text_lines.append(m.group(1).strip())
                break
        else:
            # Also capture heading text, link text, emphasis
            for pattern in [
                r'heading "(.+?)"',
                r'- emphasis:\s*(.+)',
                r'emphasis:\s*(.+)',
            ]:
                m = re.search(pattern, stripped)
                if m:
                    text_lines.append(m.group(1).strip())
                    break

    # Deduplicate consecutive identical lines
    deduped = []
    for line in text_lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)

    return title, "\n".join(deduped)


def fetch_via_camofox(url: str, port: int = 9377, wait: float = 6) -> Optional[FetchResult]:
    """Fetch any URL via Camofox browser. Returns FetchResult or None if unavailable."""
    if not _camofox_available(port):
        return None

    session_key = f"lv-{hash(url) & 0xFFFFFF:06x}-{int(time.time())}"
    print(f"[link-vault] Fetching via Camofox: {url}", file=sys.stderr)

    snapshot = camofox_fetch_page(url, session_key, wait=wait, port=port)
    if not snapshot:
        return FetchResult(ok=False, url=url, source_type=classify_url(url),
                           error="Camofox returned empty snapshot")

    title, text = _parse_snapshot_to_text(snapshot)
    source_type = classify_url(url)

    return FetchResult(
        ok=True, url=url, source_type=source_type,
        title=title, text=text,
        metadata={"fetched_via": "camofox", "raw_snapshot_len": len(snapshot)},
    )

# ---------------------------------------------------------------------------
# X/Twitter enrichment — FxTwitter API for structured stats/media
# ---------------------------------------------------------------------------

def _enrich_tweet(result: FetchResult, url: str, timeout: int = 15) -> FetchResult:
    """Enrich a tweet FetchResult with structured FxTwitter data."""
    m = _TWEET_RE.match(url)
    if not m:
        return result
    username, tweet_id = m.group(1), m.group(2)
    api_url = f"https://api.fxtwitter.com/{username}/status/{tweet_id}"

    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        if data.get("code") != 200:
            return result  # Keep Camofox data, enrichment failed silently

        tw = data["tweet"]
        # Override with structured data
        result.title = f"@{tw.get('author', {}).get('screen_name', username)}"
        result.author = tw.get("author", {}).get("name", username)
        result.text = tw.get("text", result.text)  # Prefer FxTwitter text (cleaner)

        result.metadata.update({
            "likes": tw.get("likes", 0),
            "retweets": tw.get("retweets", 0),
            "views": tw.get("views"),
            "replies_count": tw.get("replies", 0),
            "bookmarks": tw.get("bookmarks", 0),
            "created_at": tw.get("created_at", ""),
            "lang": tw.get("lang", ""),
            "is_note_tweet": tw.get("is_note_tweet", False),
        })
        # Media
        media_all = tw.get("media", {})
        if media_all and media_all.get("all"):
            result.metadata["media"] = [
                {"type": mi.get("type"), "url": mi.get("url")}
                for mi in media_all["all"]
            ]
        # Quote
        qt = tw.get("quote")
        if qt:
            result.metadata["quote"] = {
                "text": qt.get("text", ""),
                "author": qt.get("author", {}).get("screen_name", ""),
                "url": qt.get("url", ""),
            }
        # Article
        article = tw.get("article")
        if article:
            blocks = article.get("content", {}).get("blocks", [])
            full = "\n\n".join(b.get("text", "") for b in blocks if b.get("text"))
            result.metadata["article"] = {
                "title": article.get("title", ""),
                "full_text": full,
                "word_count": len(full.split()) if full else 0,
            }
    except Exception:
        pass  # Enrichment is best-effort
    return result

# ---------------------------------------------------------------------------
# Tweet-only fallback (when Camofox is unavailable)
# ---------------------------------------------------------------------------

def fetch_tweet(url: str, timeout: int = 15, retries: int = 2) -> FetchResult:
    """Fetch tweet via FxTwitter API only (no Camofox)."""
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
            media_all = tw.get("media", {})
            if media_all and media_all.get("all"):
                meta["media"] = [{"type": mi.get("type"), "url": mi.get("url")}
                                 for mi in media_all["all"]]
            qt = tw.get("quote")
            if qt:
                meta["quote"] = {
                    "text": qt.get("text", ""),
                    "author": qt.get("author", {}).get("screen_name", ""),
                    "url": qt.get("url", ""),
                }
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
# YouTube fetcher (yt-dlp for metadata + transcript)
# ---------------------------------------------------------------------------

def fetch_youtube(url: str, timeout: int = 30, **kwargs) -> FetchResult:
    m = _YT_RE.match(url)
    video_id = m.group(1) if m else ""
    canonical = f"https://www.youtube.com/watch?v={video_id}" if video_id else url

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

    transcript = ""
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["yt-dlp", "--write-auto-sub", "--sub-lang", "en,zh,ja,ko",
                 "--skip-download", "--sub-format", "vtt",
                 "-o", f"{tmpdir}/sub", url],
                capture_output=True, text=True, timeout=timeout,
            )
            for f in Path(tmpdir).glob("*.vtt"):
                raw = f.read_text(errors="replace")
                lines = []
                for line in raw.splitlines():
                    if re.match(r"^\d{2}:\d{2}:", line) or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:") or not line.strip():
                        continue
                    clean = re.sub(r"<\d{2}:\d{2}:[\d.]+>", "", line).strip()
                    if clean and (not lines or lines[-1] != clean):
                        lines.append(clean)
                transcript = "\n".join(lines)
                break
    except Exception:
        pass

    # Fallback: use faster-whisper if no subtitles found
    if not transcript:
        try:
            from .transcription import transcribe_url as _whisper_transcribe
            transcribe_config = kwargs.get("transcribe_config")
            whisper_text = _whisper_transcribe(url, config=transcribe_config)
            if whisper_text:
                transcript = whisper_text
                transcript_method = "whisper"
        except Exception:
            pass

    if not transcript:
        transcript_method = None
    elif "transcript_method" not in dir():
        transcript_method = "subtitles"

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
        "transcript_method": transcript_method,
    }

    return FetchResult(
        ok=True, url=canonical, source_type="youtube",
        title=title, author=author,
        text="\n\n".join(text_parts),
        metadata=meta,
    )

# ---------------------------------------------------------------------------
# Generic video fetcher (yt-dlp metadata + faster-whisper transcription)
# ---------------------------------------------------------------------------

def fetch_video(url: str, timeout: int = 30, **kwargs) -> FetchResult:
    """Fetch video metadata via yt-dlp and transcribe audio with faster-whisper."""
    source_type = classify_url(url)

    # Step 1: metadata via yt-dlp
    try:
        proc = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", "--no-playlist", url],
            capture_output=True, text=True, timeout=timeout,
        )
        if proc.returncode != 0:
            return FetchResult(ok=False, url=url, source_type=source_type,
                               error=f"yt-dlp metadata failed: {proc.stderr[:300]}")
        info = json.loads(proc.stdout)
    except FileNotFoundError:
        return FetchResult(ok=False, url=url, source_type=source_type,
                           error="yt-dlp not installed")
    except subprocess.TimeoutExpired:
        return FetchResult(ok=False, url=url, source_type=source_type,
                           error="yt-dlp timed out")
    except json.JSONDecodeError:
        return FetchResult(ok=False, url=url, source_type=source_type,
                           error="yt-dlp returned invalid JSON")

    title = info.get("title", "")
    author = info.get("uploader", info.get("channel", ""))
    description = info.get("description", "")
    canonical = info.get("webpage_url", url)

    # Step 2: transcribe audio with faster-whisper
    transcript = None
    transcript_method = None
    transcribe_config = kwargs.get("transcribe_config")
    try:
        from .transcription import transcribe_url as _whisper_transcribe
        transcript = _whisper_transcribe(url, config=transcribe_config)
        if transcript:
            transcript_method = "whisper"
    except Exception as e:
        print(f"[link-vault] Transcription skipped: {e}", file=sys.stderr)

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
        "has_transcript": bool(transcript),
        "transcript_method": transcript_method,
        "platform": info.get("extractor", source_type),
    }

    return FetchResult(
        ok=True, url=canonical, source_type=source_type,
        title=title, author=author,
        text="\n\n".join(text_parts),
        metadata=meta,
    )


# ---------------------------------------------------------------------------
# Generic webpage fallback (readability + bs4, no Camofox)
# ---------------------------------------------------------------------------

def _decompress_response(raw: bytes, encoding: str) -> bytes:
    """Decompress HTTP response body based on Content-Encoding header."""
    enc = (encoding or "").strip().lower()
    if enc == "gzip" or enc == "x-gzip":
        import gzip
        return gzip.decompress(raw)
    if enc == "deflate":
        import zlib
        try:
            return zlib.decompress(raw)
        except zlib.error:
            return zlib.decompress(raw, -zlib.MAX_WBITS)
    if enc == "br":
        try:
            import brotli
            return brotli.decompress(raw)
        except ImportError:
            raise ValueError("Brotli encoding but 'brotli' package not installed")
    return raw


def _looks_like_text(text: str, sample_size: int = 1024) -> bool:
    """Heuristic: return False if the string looks like binary garbage / mojibake."""
    if not text:
        return True  # empty is fine
    sample = text[:sample_size]
    # Count Unicode replacement characters and control chars (excluding common whitespace)
    bad = sum(1 for ch in sample if ch == '\ufffd' or (ord(ch) < 32 and ch not in '\n\r\t'))
    ratio = bad / len(sample)
    return ratio < 0.05  # less than 5% garbage chars → likely real text


def fetch_webpage(url: str, timeout: int = 15) -> FetchResult:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; LinkVault/0.1)",
            "Accept-Encoding": "gzip, deflate",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
            content_encoding = resp.headers.get("Content-Encoding", "")
            final_url = resp.url

        # Decompress if needed
        try:
            raw_bytes = _decompress_response(raw_bytes, content_encoding)
        except Exception as e:
            return FetchResult(ok=False, url=url, source_type="webpage",
                               error=f"Decompression failed ({content_encoding}): {e}")

        # Detect charset from Content-Type, default to utf-8
        ct = resp.headers.get("Content-Type", "")
        charset = "utf-8"
        for part in ct.split(";"):
            part = part.strip()
            if part.lower().startswith("charset="):
                charset = part.split("=", 1)[1].strip().strip('"')
                break

        html = raw_bytes.decode(charset, errors="replace")
    except Exception as e:
        return FetchResult(ok=False, url=url, source_type="webpage",
                           error=f"Fetch failed: {e}")

    title = ""
    text = ""

    try:
        from readability import Document
        doc = Document(html)
        title = doc.title()
        summary_html = doc.summary()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(summary_html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
    except Exception:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            title = soup.title.string if soup.title else ""
            text = soup.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text)
        except Exception as e2:
            return FetchResult(ok=False, url=url, source_type="webpage",
                               error=f"Parse failed: {e2}")

    # Gate: reject garbled / binary content
    if text and not _looks_like_text(text):
        return FetchResult(
            ok=False, url=url, source_type="webpage",
            title=title or "",
            error="Extracted text appears to be binary/garbled (not readable)",
            metadata={"final_url": final_url},
        )

    meta = {"final_url": final_url}
    return FetchResult(
        ok=True, url=url, source_type="webpage",
        title=title or "", author="", text=text,
        metadata=meta,
    )

# ---------------------------------------------------------------------------
# Router — Camofox-first for ALL URLs, with enrichment + fallbacks
# ---------------------------------------------------------------------------

def fetch(url: str, camofox_port: int = 9377, **kwargs) -> FetchResult:
    """
    Fetch content from ANY URL.

    Strategy:
      1. Try Camofox first (handles everything: Reddit, X, paywalled, SPAs)
      2. Layer source-specific enrichment (FxTwitter stats, yt-dlp transcript)
      3. If Camofox unavailable, fall back to source-specific adapters
    """
    source = classify_url(url)

    # --- Step 1: Try Camofox for everything ---
    camofox_result = fetch_via_camofox(url, port=camofox_port)

    if camofox_result and camofox_result.ok:
        # Step 2: Layer enrichment for known sources
        if source == "tweet":
            camofox_result = _enrich_tweet(camofox_result, url)
        elif source == "youtube":
            # Merge yt-dlp data (transcript, metadata) into Camofox result
            yt_result = fetch_youtube(url, **{k: v for k, v in kwargs.items()
                                              if k in ("timeout", "transcribe_config")})
            if yt_result.ok:
                camofox_result.title = yt_result.title or camofox_result.title
                camofox_result.author = yt_result.author or camofox_result.author
                # Append transcript to Camofox text if not already there
                if yt_result.metadata.get("has_transcript") and "Transcript" not in camofox_result.text:
                    camofox_result.text += "\n\n" + yt_result.text
                camofox_result.metadata.update(yt_result.metadata)
        elif source == "bilibili":
            # Merge yt-dlp metadata + whisper transcript into Camofox result
            vid_result = fetch_video(url, **{k: v for k, v in kwargs.items()
                                             if k in ("timeout", "transcribe_config")})
            if vid_result.ok:
                camofox_result.title = vid_result.title or camofox_result.title
                camofox_result.author = vid_result.author or camofox_result.author
                camofox_result.source_type = vid_result.source_type
                if vid_result.metadata.get("has_transcript") and "Transcript" not in camofox_result.text:
                    camofox_result.text += "\n\n" + vid_result.text
                camofox_result.metadata.update(vid_result.metadata)
        return camofox_result

    # --- Step 3: Fallbacks when Camofox is unavailable ---
    if source == "tweet":
        return fetch_tweet(url, **{k: v for k, v in kwargs.items() if k in ("timeout", "retries")})
    elif source == "youtube":
        return fetch_youtube(url, **{k: v for k, v in kwargs.items()
                                     if k in ("timeout", "transcribe_config")})
    elif source == "bilibili":
        return fetch_video(url, **{k: v for k, v in kwargs.items()
                                   if k in ("timeout", "transcribe_config")})
    else:
        return fetch_webpage(url, **{k: v for k, v in kwargs.items() if k in ("timeout",)})


def fetch_batch(urls: List[str], **kwargs) -> List[FetchResult]:
    """Fetch multiple URLs."""
    return [fetch(url, **kwargs) for url in urls]
