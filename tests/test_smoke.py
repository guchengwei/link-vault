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
    test("CLI ingest", test_cli_ingest)
    test("CLI search", test_cli_search)
    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    sys.exit(0 if FAIL == 0 else 1)
