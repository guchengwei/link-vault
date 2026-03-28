# link-vault

General-purpose link content fetcher with vector search. Give it **any URL** — tweets, Reddit posts, YouTube videos, news articles, SPAs — and it fetches the content, saves as Markdown, indexes in a local SQLite vector database, and syncs to GitHub weekly.

## How It Works

```
Any URL ──► Camofox (browser) ──► content + enrichment ──► Markdown + SQLite vectors
              │ unavailable?
              ▼
         Fallback adapters
         (FxTwitter / yt-dlp / readability)
```

**Camofox is the primary engine for ALL URLs.** It renders pages in a real anti-detection browser (via x-tweet-fetcher's `camofox_client`), so it handles JavaScript-rendered sites, paywalled content, Reddit, X/Twitter, and anything a browser can load. Source-specific enrichment (tweet stats, YouTube transcripts) is layered on top.

When Camofox isn't running, per-source fallbacks kick in automatically.

## Quickstart

```bash
# Ingest ANY URL
python -m linkvault ingest https://x.com/jack/status/20
python -m linkvault ingest https://www.reddit.com/r/MachineLearning/comments/abc123/
python -m linkvault ingest https://www.youtube.com/watch?v=dQw4w9WgXcQ
python -m linkvault ingest https://example.com/interesting-article

# Batch ingest
python -m linkvault ingest url1 url2 url3

# Semantic search
python -m linkvault search "machine learning"

# List / Stats
python -m linkvault list
python -m linkvault stats
```

## Output Modes

```bash
# Human-readable (default)
python -m linkvault search "topic"

# JSON output
python -m linkvault --json search "topic"
python -m linkvault --json ingest https://x.com/jack/status/20
```

## Architecture

```
link-vault/
├── linkvault/
│   ├── __init__.py        # Package
│   ├── __main__.py        # python -m entry
│   ├── cli.py             # CLI (ingest/search/list/stats)
│   ├── fetchers.py        # Camofox-first router + source adapters
│   ├── storage.py         # Markdown output + organized file storage
│   └── vectordb.py        # SQLite vector DB (chunk, embed, search)
├── content/               # Stored Markdown files (auto-created)
│   ├── tweets/YYYY-MM/
│   ├── youtube/YYYY-MM/
│   ├── reddit/YYYY-MM/
│   └── web/YYYY-MM/
├── scripts/
│   ├── weekly-push.sh     # Git commit + push content weekly
│   └── install-cron.sh    # Install weekly cron job
├── tests/
│   └── test_smoke.py      # 9 smoke tests
├── linkvault.db           # SQLite database (auto-created)
└── README.md
```

### Fetch Strategy

| Priority | Engine | Handles | Dependencies |
|----------|--------|---------|-------------|
| 1 (primary) | **Camofox** | **Any URL** — Reddit, X, SPAs, paywalled sites | Camofox on localhost:9377 |
| 2 (enrichment) | FxTwitter API | X/Twitter stats, media, quotes, articles | None (stdlib) |
| 2 (enrichment) | yt-dlp | YouTube metadata + transcript | yt-dlp |
| 3 (fallback) | readability + bs4 | Generic web when Camofox unavailable | readability-lxml, beautifulsoup4 |

### Vector Search

- **Embedding model:** `all-MiniLM-L6-v2` (384-dim, via torch + transformers)
- **Storage:** SQLite with embeddings as float32 blobs (no extensions needed)
- **Search:** Cosine similarity via numpy (fast for thousands of documents)
- **Chunking:** Paragraph-aware, 800-char chunks with 100-char overlap

## Weekly GitHub Sync

```bash
# One-time setup: install cron job (Sundays 3am)
bash scripts/install-cron.sh

# Or run manually
bash scripts/weekly-push.sh
```

## Dependencies

- Python 3.7+
- `torch` + `transformers` — embeddings
- `numpy` — vector operations
- `beautifulsoup4` + `readability-lxml` — HTML parsing (fallback)
- `yt-dlp` — YouTube metadata + transcript (optional)
- **Camofox** on `localhost:9377` — primary fetch engine (optional but recommended)

## Smoke Tests

```bash
python tests/test_smoke.py
```

## CLI Options

| Flag | Description |
|------|-------------|
| `--db PATH` | SQLite database path (default: `linkvault.db`) |
| `--content-dir DIR` | Content storage directory (default: `content/`) |
| `--json` | JSON output |
| `--top-k N` | Number of search results (default: 5) |
