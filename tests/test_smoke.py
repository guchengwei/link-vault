#!/usr/bin/env python3
"""Smoke tests for xfetch-backed link-vault."""

import json
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


def test_chunking():
    from linkvault.vectordb import chunk_text
    short = "Hello world"
    assert chunk_text(short) == [short]
    long_text = ("Word " * 200 + "\n\n") * 5
    chunks = chunk_text(long_text, max_chars=500)
    assert len(chunks) > 1
    assert all(chunks)


def test_bundle_loading():
    from linkvault.xfetch_adapter import load_bundle, bundle_index_text
    payload = load_bundle(str(FIXTURE_BUNDLE))
    assert payload["document"]["title"] == "Test Article About AI"
    assert payload["index_path"].endswith("index.md")
    assert "machine learning" in bundle_index_text(str(FIXTURE_BUNDLE))


def test_vectordb():
    from linkvault.vectordb import VectorDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = VectorDB(db_path)
        doc_id = db.ingest(
            url="https://example.com/test-article",
            source_type="webpage",
            title="Test Article About AI",
            author="Test Author",
            text="Artificial intelligence and machine learning are transforming the world.",
            metadata={"test": True},
            md_path="/tmp/index.md",
            bundle_path="/tmp/bundle",
            index_path="/tmp/index.md",
            public_url="https://example.com/public",
            publish_status="published",
        )
        assert doc_id > 0
        results = db.search("machine learning", top_k=3)
        assert results
        doc = db.get_document_by_url("https://example.com/test-article")
        assert doc["bundle_path"] == "/tmp/bundle"
        assert doc["publish_status"] == "published"
        db.close()


def test_cli_ingest_partial_success():
    from linkvault import cli
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "cli.db")
        args = type("Args", (), {
            "urls": ["https://example.com/test-article"],
            "db": db_path,
            "content_dir": tmpdir,
            "json": True,
        })
        with mock.patch("linkvault.cli.ingest_url", return_value={"url": "https://example.com/test-article", "bundle_path": str(FIXTURE_BUNDLE)}), \
             mock.patch("linkvault.cli.publish_bundle", side_effect=cli.XFetchError("publish broke")):
            from io import StringIO
            old = sys.stdout
            sys.stdout = StringIO()
            try:
                cli.cmd_ingest(args)
                out = sys.stdout.getvalue()
            finally:
                sys.stdout = old
        data = json.loads(out)
        assert data[0]["ok"] is True
        assert data[0]["published"] is False
        assert data[0]["publish_error"] == "publish broke"


def test_cli_ingest_success():
    from linkvault import cli
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "cli.db")
        args = type("Args", (), {
            "urls": ["https://example.com/test-article"],
            "db": db_path,
            "content_dir": tmpdir,
            "json": True,
        })
        with mock.patch("linkvault.cli.ingest_url", return_value={"url": "https://example.com/test-article", "bundle_path": str(FIXTURE_BUNDLE)}), \
             mock.patch("linkvault.cli.publish_bundle", return_value={"ok": True, "public_url": "https://example.com/public"}):
            from io import StringIO
            old = sys.stdout
            sys.stdout = StringIO()
            try:
                cli.cmd_ingest(args)
                out = sys.stdout.getvalue()
            finally:
                sys.stdout = old
        data = json.loads(out)
        assert data[0]["published"] is True
        assert data[0]["public_url"] == "https://example.com/public"


if __name__ == "__main__":
    print("=== xfetch-backed link-vault smoke tests ===\n")
    test("Text chunking", test_chunking)
    test("Bundle loading", test_bundle_loading)
    test("Vector DB ingest+search", test_vectordb)
    test("CLI ingest partial success", test_cli_ingest_partial_success)
    test("CLI ingest success", test_cli_ingest_success)
    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(0 if FAIL == 0 else 1)
