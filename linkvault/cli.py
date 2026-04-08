#!/usr/bin/env python3
"""
link-vault CLI, ingest URLs and search stored xfetch bundle content.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from .vectordb import VectorDB
from .xfetch_adapter import XFetchError, ingest_url, load_bundle, publish_bundle

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


def _extract_doc_fields(ingest_payload: dict, bundle_payload: dict) -> dict:
    document = bundle_payload.get("document") or {}
    index_path = bundle_payload.get("index_path", "")
    index_text = bundle_payload.get("index_text", "")
    title = document.get("title") or ingest_payload.get("title") or ingest_payload.get("url")
    author = document.get("author") or document.get("byline") or ingest_payload.get("author") or ""
    source_type = document.get("source_type") or ingest_payload.get("source_type") or document.get("kind") or "webpage"
    canonical_url = document.get("url") or ingest_payload.get("url")
    return {
        "url": canonical_url,
        "title": title,
        "author": author,
        "source_type": source_type,
        "text": index_text,
        "metadata": document,
        "index_path": index_path,
    }


def _ingest_one(url: str, db: VectorDB, content_dir: str) -> dict:
    ingest_payload = ingest_url(url, content_root=content_dir)
    bundle_path = ingest_payload.get("bundle_path") or ingest_payload.get("bundle") or ""
    if not bundle_path:
        raise XFetchError("xfetch ingest did not return bundle_path")

    bundle_payload = load_bundle(bundle_path)
    doc = _extract_doc_fields(ingest_payload, bundle_payload)

    published = False
    public_url = ""
    publish_error = ""
    publish_status = "not_attempted"
    try:
        publish_payload = publish_bundle(bundle_path)
        published = bool(publish_payload.get("ok", True))
        public_url = publish_payload.get("public_url") or publish_payload.get("url") or ""
        publish_status = "published" if published else "failed"
        publish_error = publish_payload.get("error") or ""
    except XFetchError as exc:
        publish_status = "failed"
        publish_error = str(exc)

    db.ingest(
        url=doc["url"],
        source_type=doc["source_type"],
        title=doc["title"],
        author=doc["author"],
        text=doc["text"],
        metadata=doc["metadata"],
        md_path=doc["index_path"],
        bundle_path=bundle_path,
        index_path=doc["index_path"],
        public_url=public_url,
        publish_status=publish_status,
        publish_error=publish_error,
    )

    return {
        "ok": True,
        "url": doc["url"],
        "title": doc["title"],
        "source_type": doc["source_type"],
        "bundle_path": bundle_path,
        "index_path": doc["index_path"],
        "published": published,
        "public_url": public_url,
        "error": None,
        "publish_error": publish_error or None,
    }


def cmd_ingest(args):
    _log.info("ingest called | urls=%s | db=%s | content_dir=%s | cwd=%s", args.urls, args.db, args.content_dir, os.getcwd())
    db = VectorDB(args.db)
    results = []
    for url in args.urls:
        print(f"Ingesting via xfetch: {url} ...", file=sys.stderr)
        try:
            results.append(_ingest_one(url, db, args.content_dir))
        except XFetchError as exc:
            results.append({
                "ok": False,
                "url": url,
                "title": "",
                "source_type": "",
                "bundle_path": "",
                "index_path": "",
                "published": False,
                "public_url": "",
                "error": str(exc),
                "publish_error": None,
            })
    db.close()

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if not r["ok"]:
                print(f"Save failed: {r['url']} -> {r['error']}")
            elif r["published"]:
                print(f"Saved + published: {r['title']} -> {r['public_url']}")
            else:
                print(f"Saved locally, publish failed: {r['title']} -> {r['publish_error']}")


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
            if r.get("public_url"):
                print(f"    Public: {r['public_url']}")
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
            if d.get("public_url"):
                print(f"    {d['public_url']}")


def cmd_stats(args):
    db = VectorDB(args.db)
    s = db.stats()
    db.close()
    print(json.dumps(s, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="linkvault", description="Link content vault, ingest, store, and search.")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"SQLite database path (default: {DEFAULT_DB})")
    parser.add_argument("--content-dir", default=DEFAULT_CONTENT_DIR, help="xfetch content root / bundle directory")
    parser.add_argument("--json", action="store_true", help="JSON output")

    sub = parser.add_subparsers(dest="command")
    p_ingest = sub.add_parser("ingest", help="Ingest, publish, and index URLs via xfetch")
    p_ingest.add_argument("urls", nargs="+", help="URL(s) to ingest")
    p_search = sub.add_parser("search", help="Semantic search across indexed bundle content")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--top-k", type=int, default=5, help="Number of results")
    sub.add_parser("list", help="List ingested documents")
    sub.add_parser("stats", help="Show database stats")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"ingest": cmd_ingest, "search": cmd_search, "list": cmd_list, "stats": cmd_stats}[args.command](args)


if __name__ == "__main__":
    main()
