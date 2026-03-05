# link-vault

Ingest, store, and semantically search web content. Fetches any URL — tweets, YouTube videos, web articles — saves as Markdown, indexes in a local SQLite vector database, and syncs to GitHub weekly.

## Quickstart

```bash
# Ingest a tweet
python -m linkvault ingest https://x.com/jack/status/20

# Ingest a YouTube video (metadata + transcript)
python -m linkvault ingest https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Ingest a webpage
python -m linkvault ingest https://example.com/interesting-article

# Batch ingest
python -m linkvault ingest url1 url2 url3

# Semantic search
python -m linkvault search "machine learning"

# List all ingested documents
python -m linkvault list

# Show stats
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
│   ├── fetchers.py        # URL adapters (tweet, youtube, webpage)
│   ├── storage.py         # Markdown output + organized file storage
│   └── vectordb.py        # SQLite vector DB (chunk, embed, search)
├── content/               # Stored Markdown files (auto-created)
│   ├── tweets/YYYY-MM/
│   ├── youtube/YYYY-MM/
│   └── web/YYYY-MM/
├── scripts/
│   ├── weekly-push.sh     # Git commit + push content weekly
│   └── install-cron.sh    # Install weekly cron job
├── tests/
│   └── test_smoke.py      # 9 smoke tests
├── linkvault.db           # SQLite database (auto-created)
└── README.md
```

### Fetcher Adapters

| Source | Detection | Backend | Dependencies |
|--------|-----------|---------|-------------|
| X/Twitter | `x.com/*/status/*`, `twitter.com/*/status/*` | FxTwitter API | None (stdlib) |
| YouTube | `youtube.com/watch?v=*`, `youtu.be/*` | yt-dlp | yt-dlp |
| Generic web | Everything else | readability + BeautifulSoup | readability-lxml, beautifulsoup4 |

### Vector Search

- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, loaded via torch + transformers)
- **Storage:** SQLite with embeddings as float32 blobs (no extensions needed)
- **Search:** Brute-force cosine similarity via numpy (fast enough for thousands of documents)
- **Chunking:** Paragraph-aware with 800-char chunks and 100-char overlap

## Weekly GitHub Sync

```bash
# One-time setup: install cron job (Sundays 3am)
bash scripts/install-cron.sh

# Or run manually
bash scripts/weekly-push.sh
```

The pipeline commits all new `content/` files and the database, then pushes to origin.

## Dependencies

- Python 3.7+
- `torch` — embedding computation
- `transformers` — tokenizer + model loading
- `numpy` — vector operations
- `beautifulsoup4` — HTML parsing
- `readability-lxml` — article extraction
- `yt-dlp` — YouTube metadata + transcript (optional)

## Smoke Tests

```bash
python tests/test_smoke.py
```

## Options

| Flag | Description |
|------|-------------|
| `--db PATH` | SQLite database path (default: `linkvault.db`) |
| `--content-dir DIR` | Content storage directory (default: `content/`) |
| `--json` | JSON output |
| `--top-k N` | Number of search results (default: 5) |
