#!/usr/bin/env python3
"""
link-vault MCP server — expose ingest, search, list, stats, get as MCP tools.

Run: python -m linkvault.mcp_server
Config via env vars:
  LINKVAULT_DB          — SQLite path (default: linkvault.db)
  LINKVAULT_CONTENT_DIR — content dir (default: content)
"""

import json
import os
from typing import Optional

from fastmcp import FastMCP

from .fetchers import fetch
from .storage import save_result
from .vectordb import VectorDB

mcp = FastMCP("link-vault", instructions="Content vault — ingest URLs, search by meaning.")

_DB = os.environ.get("LINKVAULT_DB", "linkvault.db")
_CONTENT_DIR = os.environ.get("LINKVAULT_CONTENT_DIR", "content")


def _ingest(urls: list[str], db_path: str = _DB, content_dir: str = _CONTENT_DIR) -> dict:
    db = VectorDB(db_path)
    results, errors = [], []
    for url in urls:
        r = fetch(url)
        if not r.ok:
            errors.append({"url": url, "error": r.error})
            continue
        md_path = save_result(r, base_dir=content_dir)
        doc_id = db.ingest(
            url=r.url, source_type=r.source_type, title=r.title,
            author=r.author, text=r.text, metadata=r.metadata,
            md_path=md_path or "",
        )
        results.append({
            "url": r.url, "title": r.title,
            "source_type": r.source_type, "md_path": md_path,
        })
    db.close()
    return {"ok": len(errors) == 0, "results": results, "errors": errors}


def _search(query: str, top_k: int = 5, db_path: str = _DB) -> dict:
    db = VectorDB(db_path)
    results = db.search(query, top_k=top_k)
    db.close()
    return {"results": results}


def _list_documents(source_type: Optional[str] = None, db_path: str = _DB) -> dict:
    db = VectorDB(db_path)
    docs = db.list_documents()
    db.close()
    if source_type:
        docs = [d for d in docs if d["source_type"] == source_type]
    return {"documents": docs}


def _stats(db_path: str = _DB) -> dict:
    db = VectorDB(db_path)
    s = db.stats()
    db.close()
    return s


def _get_document(url: str, db_path: str = _DB) -> dict:
    db = VectorDB(db_path)
    doc = db.get_document_by_url(url)
    db.close()
    if not doc:
        return {"error": f"No document found for URL: {url}"}
    return doc


# --- MCP tool wrappers (thin, call internal functions) ---

@mcp.tool
def ingest(urls: list[str]) -> str:
    """Fetch, save, and index one or more URLs into the link vault."""
    return json.dumps(_ingest(urls), ensure_ascii=False)


@mcp.tool
def search(query: str, top_k: int = 5) -> str:
    """Semantic search across all saved content. Returns ranked results."""
    return json.dumps(_search(query, top_k), ensure_ascii=False)


@mcp.tool
def list_documents(source_type: str = "") -> str:
    """List all ingested documents. Optionally filter by source_type (tweet, youtube, reddit, webpage)."""
    return json.dumps(_list_documents(source_type or None), ensure_ascii=False)


@mcp.tool
def stats() -> str:
    """Show vault statistics: document count, chunk count, database size."""
    return json.dumps(_stats(), ensure_ascii=False)


@mcp.tool
def get_document(url: str) -> str:
    """Retrieve a specific saved document by its URL."""
    return json.dumps(_get_document(url), ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
