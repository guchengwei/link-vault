#!/usr/bin/env python3
"""Tests for transcription module and video fetching. Run: python tests/test_transcription.py"""

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


# ---- URL classification: Bilibili ----
def test_classify_bilibili():
    from linkvault.fetchers import classify_url
    assert classify_url("https://www.bilibili.com/video/BV1PDcdzSEwP/") == "bilibili"
    assert classify_url("https://bilibili.com/video/BV1abc123") == "bilibili"
    # Non-video bilibili pages should be webpage
    assert classify_url("https://www.bilibili.com/read/cv12345") == "webpage"


# ---- URL classification: existing types unchanged ----
def test_classify_unchanged():
    from linkvault.fetchers import classify_url
    assert classify_url("https://x.com/jack/status/20") == "tweet"
    assert classify_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert classify_url("https://example.com/article") == "webpage"


# ---- TranscriptionConfig defaults ----
def test_config_defaults():
    from linkvault.transcription import TranscriptionConfig
    config = TranscriptionConfig()
    assert config.model_size == "small"
    assert config.device == "auto"
    assert config.language == "auto"
    assert config.audio_timeout == 120


# ---- TranscriptionConfig is immutable ----
def test_config_frozen():
    from linkvault.transcription import TranscriptionConfig
    config = TranscriptionConfig()
    try:
        config.model_size = "tiny"
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass  # Expected — frozen dataclass


# ---- download_audio returns None on invalid URL ----
def test_download_audio_bad_url():
    from linkvault.transcription import download_audio
    with tempfile.TemporaryDirectory() as tmpdir:
        result = download_audio("https://example.com/not-a-video", tmpdir, timeout=10)
        assert result is None


# ---- transcribe_url returns None when download fails ----
def test_transcribe_url_bad_url():
    from linkvault.transcription import TranscriptionConfig, transcribe_url
    config = TranscriptionConfig(audio_timeout=10)
    result = transcribe_url("https://example.com/not-a-video", config=config)
    assert result is None


# ---- Storage: bilibili goes to video/ dir ----
def test_storage_bilibili():
    from linkvault.fetchers import FetchResult
    from linkvault.storage import save_result
    with tempfile.TemporaryDirectory() as tmpdir:
        result = FetchResult(
            ok=True,
            url="https://www.bilibili.com/video/BV1PDcdzSEwP/",
            source_type="bilibili",
            title="Test Video",
            author="TestUser",
            text="Some transcript text",
            metadata={"has_transcript": True},
        )
        path = save_result(result, base_dir=tmpdir)
        assert path is not None
        assert "/video/" in path
        assert "BV1PDcdzSEwP" in path
        assert path.endswith(".md")
        # Verify content
        with open(path) as f:
            content = f.read()
        assert "source_type: bilibili" in content
        assert "Test Video" in content


# ---- fetch_video returns FetchResult ----
def test_fetch_video_metadata():
    """Test that fetch_video extracts metadata via yt-dlp (skipping transcription)."""
    from linkvault.fetchers import fetch_video
    from linkvault.transcription import TranscriptionConfig
    # Use --no-transcribe equivalent by not passing config
    result = fetch_video(
        "https://www.bilibili.com/video/BV1PDcdzSEwP/",
        timeout=30,
    )
    # Should succeed with yt-dlp metadata even without transcription
    if result.ok:
        assert result.source_type == "bilibili"
        assert result.title  # Should have a title
        assert "duration" in result.metadata
    else:
        # yt-dlp may fail due to network/geo restrictions — that's OK for CI
        print(f"(skipped: {result.error})", end=" ")


if __name__ == "__main__":
    print("=== Transcription & Video Tests ===")
    test("classify_bilibili", test_classify_bilibili)
    test("classify_unchanged", test_classify_unchanged)
    test("config_defaults", test_config_defaults)
    test("config_frozen", test_config_frozen)
    test("download_audio_bad_url", test_download_audio_bad_url)
    test("transcribe_url_bad_url", test_transcribe_url_bad_url)
    test("storage_bilibili", test_storage_bilibili)
    test("fetch_video_metadata", test_fetch_video_metadata)
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
