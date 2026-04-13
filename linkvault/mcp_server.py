#!/usr/bin/env python3
"""link-vault MCP server, xfetch-backed ingest and local semantic search."""

import json
import os
from typing import Optional

from fastmcp import FastMCP

from .vectordb import VectorDB
from .xfetch_adapter import XFetchError, ingest_url, load_bundle, publish_bundle

mcp = FastMCP("link-vault", instructions="Content vault, ingest URLs through xfetch and search saved bundle content.")

_DB = os.environ.get("LINKVAULT_DB", "linkvault.db")
_CONTENT_DIR = os.environ.get("LINKVAULT_CONTENT_DIR", "content")


def _extract_doc_fields(ingest_payload: dict, bundle_payload: dict) -> dict:
    document = bundle_payload.get("document") or {}
    return {
        "url": document.get("url") or ingest_payload.get("url"),
        "title": document.get("title") or ingest_payload.get("title") or ingest_payload.get("url"),
        "author": document.get("author") or document.get("byline") or ingest_payload.get("author") or "",
        "source_type": document.get("source_type") or ingest_payload.get("source_type") or document.get("kind") or "webpage",
        "text": bundle_payload.get("index_text", ""),
        "metadata": document,
        "index_path": bundle_payload.get("index_path", ""),
    }



def _index_document(db: VectorDB, doc: dict, bundle_path: str, public_url: str, publish_status: str, publish_error: str) -> tuple[str, str]:
    try:
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
        return "indexed", ""
    except Exception as exc:
        return "failed", str(exc)



def _ingest(urls: list[str], db_path: str = _DB, content_dir: str = _CONTENT_DIR) -> dict:
    db = VectorDB(db_path)
    results = []
    for url in urls:
        try:
            ingest_payload = ingest_url(url, content_root=content_dir)
            bundle_path = ingest_payload.get("bundle_path") or ingest_payload.get("bundle") or ""
            if not bundle_path:
                raise XFetchError("xfetch ingest did not return bundle_path")
            bundle_payload = load_bundle(bundle_path)
            doc = _extract_doc_fields(ingest_payload, bundle_payload)

            published = False
            public_url = ""
            publish_error = ""
            publish_status = "failed"
            try:
                publish_payload = publish_bundle(bundle_path)
                published = bool(publish_payload.get("ok", True))
                public_url = publish_payload.get("public_url") or publish_payload.get("url") or ""
                publish_error = publish_payload.get("error") or ""
                publish_status = "published" if published else "failed"
            except Exception as exc:
                publish_error = str(exc)

            index_status, index_error = _index_document(
                db,
                doc,
                bundle_path=bundle_path,
                public_url=public_url,
                publish_status=publish_status,
                publish_error=publish_error,
            )
            results.append({
                "url": doc["url"],
                "title": doc["title"],
                "source_type": doc["source_type"],
                "bundle_path": bundle_path,
                "index_path": doc["index_path"],
                "published": published,
                "public_url": public_url,
                "error": None,
                "publish_error": publish_error or None,
                "index_status": index_status,
                "index_error": index_error or None,
            })
        except XFetchError as exc:
            results.append({
                "url": url,
                "title": "",
                "source_type": "",
                "bundle_path": "",
                "index_path": "",
                "published": False,
                "public_url": "",
                "error": str(exc),
                "publish_error": None,
                "index_status": None,
                "index_error": None,
            })
    db.close()
    return {"ok": all(not r["error"] for r in results), "results": results}


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


@mcp.tool
def ingest(urls: list[str]) -> str:
    """Ingest, publish, and index one or more URLs into the link vault."""
    return json.dumps(_ingest(urls), ensure_ascii=False)


@mcp.tool
def search(query: str, top_k: int = 5) -> str:
    """Semantic search across all saved bundle content. Returns ranked results."""
    return json.dumps(_search(query, top_k), ensure_ascii=False)


@mcp.tool
def list_documents(source_type: str = "") -> str:
    """List all ingested documents. Optionally filter by source_type."""
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
