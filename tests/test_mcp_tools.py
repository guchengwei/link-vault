#!/usr/bin/env python3
"""Smoke tests for MCP server tools (direct function calls, no MCP protocol)."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0


def test(name, fn):
    global PASS, FAIL
    print(f"  {name} ... ", end="", flush=True)
    try:
        fn()
        print("PASS")
        PASS += 1
    except Exception as e:
        print(f"FAIL: {e}")
        FAIL += 1


def test_search_tool():
    """Search tool returns results after ingest."""
    from linkvault.mcp_server import _ingest, _search, _list_documents, _stats, _get_document
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        content_dir = os.path.join(tmpdir, "content")

        # Seed DB directly (bypass network)
        from linkvault.vectordb import VectorDB
        db = VectorDB(db_path)
        db.ingest(
            url="https://example.com/test-article",
            source_type="webpage",
            title="Test Article About AI",
            author="Test Author",
            text="Artificial intelligence and machine learning are transforming the world.",
            metadata={"test": True},
            md_path="",
        )
        db.close()

        # Search
        result = _search("artificial intelligence", top_k=3, db_path=db_path)
        assert len(result["results"]) > 0
        assert result["results"][0]["score"] > 0.3
        assert "AI" in result["results"][0]["title"]

        # List
        result = _list_documents(db_path=db_path)
        assert len(result["documents"]) == 1
        assert result["documents"][0]["url"] == "https://example.com/test-article"

        # Stats
        result = _stats(db_path=db_path)
        assert result["documents"] == 1
        assert result["chunks"] >= 1
        assert result["db_size_bytes"] > 0

        # Get document
        result = _get_document("https://example.com/test-article", db_path=db_path)
        assert result["title"] == "Test Article About AI"
        assert result["full_text"] is not None

        # Get missing document
        result = _get_document("https://example.com/nope", db_path=db_path)
        assert result["error"] is not None


def test_search_empty():
    """Search on empty DB returns empty results."""
    from linkvault.mcp_server import _search
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "empty.db")
        result = _search("anything", db_path=db_path)
        assert result["results"] == []


if __name__ == "__main__":
    print("=== MCP server tool tests ===\n")
    test("Search after ingest", test_search_tool)
    test("Search empty DB", test_search_empty)
    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(0 if FAIL == 0 else 1)
