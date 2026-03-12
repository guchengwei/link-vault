#!/usr/bin/env python3
"""
link-vault CLI — ingest URLs and search stored content.

Usage:
  python -m linkvault ingest <url> [url2 ...]   Fetch, save, and index URLs
  python -m linkvault search <query>             Semantic search across all content
  python -m linkvault list                       List all ingested documents
  python -m linkvault stats                      Show database stats
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .fetchers import fetch, fetch_batch, FetchResult
from .storage import save_result
from .vectordb import VectorDB

DEFAULT_DB = "linkvault.db"
DEFAULT_CONTENT_DIR = "content"
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def _setup_log():
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / "cli.log"
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    return logging.getLogger("linkvault")


_log = _setup_log()


def cmd_ingest(args):
    _log.info("ingest called | urls=%s | db=%s | content_dir=%s | cwd=%s",
              args.urls, args.db, args.content_dir, os.getcwd())
    db = VectorDB(args.db)

    # Build transcription config
    transcribe_config = None
    if not args.no_transcribe:
        from .transcription import TranscriptionConfig
        transcribe_config = TranscriptionConfig(model_size=args.whisper_model)

    results = []
    for url in args.urls:
        print(f"Fetching: {url} ...", file=sys.stderr)
        _log.info("fetching %s", url)
        result = fetch(url, transcribe_config=transcribe_config)
        if not result.ok:
            _log.error("fetch failed | url=%s | error=%s", url, result.error)
            print(f"  ERROR: {result.error}", file=sys.stderr)
            results.append(result)
            continue

        _log.info("fetch ok | url=%s | type=%s | title=%s | text_len=%d",
                   url, result.source_type, result.title, len(result.text or ""))

        # Save markdown
        md_path = save_result(result, base_dir=args.content_dir)
        _log.info("saved markdown | path=%s", md_path)
        print(f"  Saved: {md_path}", file=sys.stderr)

        # Index in vector DB
        doc_id = db.ingest(
            url=result.url,
            source_type=result.source_type,
            title=result.title,
            author=result.author,
            text=result.text,
            metadata=result.metadata,
            md_path=md_path or "",
        )
        _log.info("indexed | doc_id=%d | url=%s", doc_id, url)
        print(f"  Indexed: doc_id={doc_id}", file=sys.stderr)
        results.append(result)

    db.close()

    if args.json:
        out = [r.to_dict() for r in results]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for r in results:
            status = "OK" if r.ok else "FAIL"
            print(f"[{status}] {r.source_type}: {r.url} — {r.title or r.error}")


def cmd_search(args):
    db = VectorDB(args.db)
    results = db.search(args.query, top_k=args.top_k)
    db.close()

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No results found.")
            return
        for i, r in enumerate(results, 1):
            print(f"\n{'='*60}")
            print(f"#{i}  score={r['score']:.4f}  [{r['source_type']}]  {r['title']}")
            print(f"    URL: {r['url']}")
            print(f"    {r['chunk_text'][:300]}")


def cmd_list(args):
    db = VectorDB(args.db)
    docs = db.list_documents()
    db.close()

    if args.json:
        print(json.dumps(docs, ensure_ascii=False, indent=2))
    else:
        if not docs:
            print("No documents ingested yet.")
            return
        for d in docs:
            print(f"  [{d['source_type']}] {d['title'] or d['url']}  ({d['created_at']})")
            print(f"    {d['url']}")


def cmd_stats(args):
    db = VectorDB(args.db)
    s = db.stats()
    db.close()
    print(json.dumps(s, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="linkvault", description="Link content vault — ingest, store, and search.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"SQLite database path (default: {DEFAULT_DB})")
    parser.add_argument("--content-dir", default=DEFAULT_CONTENT_DIR, help="Content storage directory")
    parser.add_argument("--json", action="store_true", help="JSON output")

    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest", help="Fetch, save, and index URLs")
    p_ingest.add_argument("urls", nargs="+", help="URL(s) to ingest")
    p_ingest.add_argument("--whisper-model", default="small",
                          choices=["tiny", "base", "small", "medium", "large-v3"],
                          help="Whisper model size for video transcription (default: small)")
    p_ingest.add_argument("--no-transcribe", action="store_true",
                          help="Skip audio transcription for video URLs")

    p_search = sub.add_parser("search", help="Semantic search across content")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--top-k", type=int, default=5, help="Number of results")

    p_list = sub.add_parser("list", help="List ingested documents")

    p_stats = sub.add_parser("stats", help="Show database stats")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"ingest": cmd_ingest, "search": cmd_search, "list": cmd_list, "stats": cmd_stats}[args.command](args)


if __name__ == "__main__":
    main()
