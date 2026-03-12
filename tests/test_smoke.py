#!/usr/bin/env python3
"""Smoke tests for link-vault. Run: python tests/test_smoke.py"""

import json
import os
import sys
import tempfile
import shutil

# Ensure linkvault is importable
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


# ---- URL classification ----
def test_classify():
    from linkvault.fetchers import classify_url
    assert classify_url("https://x.com/jack/status/20") == "tweet"
    assert classify_url("https://twitter.com/jack/status/20") == "tweet"
    assert classify_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert classify_url("https://youtu.be/dQw4w9WgXcQ") == "youtube"
    assert classify_url("https://example.com/article") == "webpage"


# ---- Tweet fetch (live network) ----
def test_tweet_fetch():
    from linkvault.fetchers import fetch_tweet
    r = fetch_tweet("https://x.com/jack/status/20")
    assert r.ok, f"fetch failed: {r.error}"
    assert "twttr" in r.text.lower()
    assert r.source_type == "tweet"
    assert r.author


# ---- Invalid URL handling ----
def test_invalid_url():
    from linkvault.fetchers import fetch
    r = fetch("https://not-a-tweet.example.com")
    assert r.ok or r.error  # should not crash


# ---- Webpage fetch ----
def test_webpage_fetch():
    from linkvault.fetchers import fetch_webpage
    r = fetch_webpage("https://example.com")
    assert r.ok, f"fetch failed: {r.error}"
    assert r.text
    assert r.source_type == "webpage"


# ---- Chunking ----
def test_chunking():
    from linkvault.vectordb import chunk_text
    short = "Hello world"
    assert chunk_text(short) == [short]
    long_text = ("Word " * 200 + "\n\n") * 5
    chunks = chunk_text(long_text, max_chars=500)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) > 0


# ---- Markdown storage ----
def test_storage():
    from linkvault.fetchers import FetchResult
    from linkvault.storage import save_result, result_to_markdown
    r = FetchResult(ok=True, url="https://x.com/test/status/123",
                    source_type="tweet", title="@test", author="Test User",
                    text="Hello from test", metadata={"likes": 42})
    md = result_to_markdown(r)
    assert "Hello from test" in md
    assert "url:" in md

    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_result(r, base_dir=tmpdir)
        assert path and os.path.exists(path)
        content = open(path).read()
        assert "Hello from test" in content


# ---- Vector DB ingest + search ----
def test_vectordb():
    from linkvault.vectordb import VectorDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = VectorDB(db_path)

        doc_id = db.ingest(
            url="https://x.com/test/status/1",
            source_type="tweet",
            title="Test Tweet",
            author="tester",
            text="Python is a great programming language for data science and machine learning.",
            metadata={},
        )
        assert doc_id > 0

        stats = db.stats()
        assert stats["documents"] == 1
        assert stats["chunks"] >= 1

        results = db.search("machine learning programming", top_k=3)
        assert len(results) > 0
        assert results[0]["score"] > 0.3
        assert "Python" in results[0]["chunk_text"]

        db.close()


# ---- CLI (ingest + search) ----
def test_cli_ingest():
    import subprocess
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "cli.db")
        content_dir = os.path.join(tmpdir, "content")
        result = subprocess.run(
            [sys.executable, "-m", "linkvault", "--db", db_path,
             "--content-dir", content_dir, "--json", "ingest",
             "https://x.com/jack/status/20"],
            capture_output=True, text=True, timeout=60,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert data[0]["ok"]


def test_cli_search():
    import subprocess
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "cli.db")
        content_dir = os.path.join(tmpdir, "content")
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Ingest first
        subprocess.run(
            [sys.executable, "-m", "linkvault", "--db", db_path,
             "--content-dir", content_dir, "ingest",
             "https://x.com/jack/status/20"],
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        # Search
        result = subprocess.run(
            [sys.executable, "-m", "linkvault", "--db", db_path, "--json",
             "search", "twitter"],
            capture_output=True, text=True, timeout=60, cwd=cwd,
        )
        assert result.returncode == 0, f"Search failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert len(data) > 0


# ---- VectorDB get_document_by_url ----
def test_get_document():
    from linkvault.vectordb import VectorDB
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = VectorDB(db_path)
        db.ingest(
            url="https://x.com/test/status/99",
            source_type="tweet",
            title="Test Tweet",
            author="tester",
            text="This is a test document for retrieval.",
            metadata={"likes": 10},
        )
        doc = db.get_document_by_url("https://x.com/test/status/99")
        assert doc is not None
        assert doc["title"] == "Test Tweet"
        assert doc["author"] == "tester"
        assert doc["full_text"] == "This is a test document for retrieval."
        assert doc["metadata"]["likes"] == 10
        assert doc["source_type"] == "tweet"

        missing = db.get_document_by_url("https://example.com/nope")
        assert missing is None

        s = db.stats()
        assert "db_size_bytes" in s
        assert s["db_size_bytes"] > 0

        db.close()


# ---- Decompress response ----
def test_decompress_gzip():
    import gzip
    from linkvault.fetchers import _decompress_response
    original = b"<html><body>Hello Bilibili</body></html>"
    compressed = gzip.compress(original)
    assert _decompress_response(compressed, "gzip") == original
    assert _decompress_response(compressed, "x-gzip") == original
    # Identity / no encoding
    assert _decompress_response(original, "") == original
    assert _decompress_response(original, "identity") == original


def test_decompress_deflate():
    import zlib
    from linkvault.fetchers import _decompress_response
    original = b"<html><body>Test deflate</body></html>"
    compressed = zlib.compress(original)
    assert _decompress_response(compressed, "deflate") == original


# ---- Binary / garbled text detection ----
def test_looks_like_text():
    from linkvault.fetchers import _looks_like_text
    # Normal text passes
    assert _looks_like_text("Hello world, this is a normal webpage.")
    assert _looks_like_text("日本語テキストもOKです。")
    assert _looks_like_text("")  # empty is fine
    # Garbled binary fails
    garbled = "\ufffd" * 100  # all replacement chars
    assert not _looks_like_text(garbled)
    # Mixed garbled (>5% bad)
    mostly_bad = "\ufffd" * 10 + "x" * 50
    assert not _looks_like_text(mostly_bad)
    # Mostly good with a few replacements (<5%)
    mostly_good = "Normal text content here. " * 10 + "\ufffd"
    assert _looks_like_text(mostly_good)


# ---- fetch_webpage rejects garbled content ----
def test_webpage_rejects_garbled():
    """Simulate what happens when decompression works but content is still garbled."""
    from linkvault.fetchers import _looks_like_text
    # This simulates a page that, after decompression, still produces replacement chars
    garbled = "\ufffd\x01\x02" * 200
    assert not _looks_like_text(garbled), "Garbled text should be rejected"


# ---- Run all ----
if __name__ == "__main__":
    print("=== link-vault smoke tests ===\n")
    test("URL classification", test_classify)
    test("Tweet fetch (live)", test_tweet_fetch)
    test("Invalid URL handling", test_invalid_url)
    test("Webpage fetch", test_webpage_fetch)
    test("Text chunking", test_chunking)
    test("Markdown storage", test_storage)
    test("Vector DB ingest+search", test_vectordb)
    test("VectorDB get_document", test_get_document)
    test("CLI ingest", test_cli_ingest)
    test("CLI search", test_cli_search)
    test("Decompress gzip", test_decompress_gzip)
    test("Decompress deflate", test_decompress_deflate)
    test("Text vs binary detection", test_looks_like_text)
    test("Garbled content rejection", test_webpage_rejects_garbled)
    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(0 if FAIL == 0 else 1)
