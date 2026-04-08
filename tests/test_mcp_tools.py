#!/usr/bin/env python3
"""Smoke tests for MCP server tools using xfetch-backed fixtures."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0
FIXTURE_BUNDLE = Path(__file__).parent / "fixtures" / "xfetch" / "example-bundle"


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
    from linkvault.mcp_server import _ingest, _search, _list_documents, _stats, _get_document
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        with mock.patch("linkvault.mcp_server.ingest_url", return_value={"url": "https://example.com/test-article", "bundle_path": str(FIXTURE_BUNDLE)}), \
             mock.patch("linkvault.mcp_server.publish_bundle", return_value={"ok": True, "public_url": "https://example.com/public"}):
            ingest_result = _ingest(["https://example.com/test-article"], db_path=db_path, content_dir=tmpdir)
        assert ingest_result["results"][0]["published"] is True
        result = _search("artificial intelligence", top_k=3, db_path=db_path)
        assert len(result["results"]) > 0
        result = _list_documents(db_path=db_path)
        assert len(result["documents"]) == 1
        result = _stats(db_path=db_path)
        assert result["documents"] == 1
        result = _get_document("https://example.com/test-article", db_path=db_path)
        assert result["title"] == "Test Article About AI"


def test_partial_success():
    from linkvault.mcp_server import _ingest
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        with mock.patch("linkvault.mcp_server.ingest_url", return_value={"url": "https://example.com/test-article", "bundle_path": str(FIXTURE_BUNDLE)}), \
             mock.patch("linkvault.mcp_server.publish_bundle", side_effect=Exception("publish failed")):
            result = _ingest(["https://example.com/test-article"], db_path=db_path, content_dir=tmpdir)
        assert result["results"][0]["published"] is False
        assert result["results"][0]["publish_error"]


if __name__ == "__main__":
    print("=== MCP server tool tests ===\n")
    test("Search after ingest", test_search_tool)
    test("Partial success", test_partial_success)
    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(0 if FAIL == 0 else 1)
