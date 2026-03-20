#!/usr/bin/env python3

import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestB23MinimumFix(unittest.TestCase):
    def test_validate_fetch_result_rejects_verification_page(self):
        from linkvault.fetchers import FetchResult, validate_fetch_result

        result = FetchResult(
            ok=True,
            url="https://b23.tv/cMBlJvK",
            source_type="webpage",
            title="验证码_哔哩哔哩",
            text="   ",
            metadata={"final_url": "https://www.bilibili.com/opus/123"},
        )

        is_valid, reason = validate_fetch_result(result)
        self.assertFalse(is_valid)
        self.assertIn("empty body text", reason)

    def test_validate_fetch_result_accepts_normal_webpage(self):
        from linkvault.fetchers import FetchResult, validate_fetch_result

        result = FetchResult(
            ok=True,
            url="https://example.com/article",
            source_type="webpage",
            title="Example Article",
            text="This is real article text.",
            metadata={"final_url": "https://example.com/article"},
        )

        is_valid, reason = validate_fetch_result(result)
        self.assertTrue(is_valid)
        self.assertIsNone(reason)

    def test_fetch_classifies_on_resolved_url(self):
        from linkvault import fetchers

        seen = {}

        def fake_fetch_video(url, **kwargs):
            seen["url"] = url
            return fetchers.FetchResult(
                ok=True,
                url=url,
                source_type="bilibili",
                title="Video",
                text="Transcript text",
                metadata={},
            )

        with mock.patch.object(fetchers, "resolve_url", return_value="https://www.bilibili.com/video/BV1xx"), \
             mock.patch.object(fetchers, "fetch_via_camofox", return_value=None), \
             mock.patch.object(fetchers, "fetch_video", side_effect=fake_fetch_video):
            result = fetchers.fetch("https://b23.tv/cMBlJvK")

        self.assertTrue(result.ok)
        self.assertEqual(result.source_type, "bilibili")
        self.assertEqual(seen["url"], "https://www.bilibili.com/video/BV1xx")
        self.assertEqual(result.metadata["original_url"], "https://b23.tv/cMBlJvK")
        self.assertEqual(result.metadata["resolved_url"], "https://www.bilibili.com/video/BV1xx")

    def test_cli_rejects_invalid_result_before_save(self):
        from linkvault import cli
        from linkvault.fetchers import FetchResult

        saved = {"called": False}
        ingested = {"called": False}

        def fake_fetch(url, transcribe_config=None):
            return FetchResult(
                ok=True,
                url=url,
                source_type="webpage",
                title="验证码_哔哩哔哩",
                text="",
                metadata={
                    "resolved_url": "https://www.bilibili.com/opus/123",
                    "final_url": "https://www.bilibili.com/opus/123",
                },
            )

        def fake_save_result(result, base_dir):
            saved["called"] = True
            return os.path.join(base_dir, "should-not-exist.md")

        class FakeDB:
            def __init__(self, path):
                self.path = path

            def ingest(self, **kwargs):
                ingested["called"] = True
                return 1

            def close(self):
                return None

        with tempfile.TemporaryDirectory() as tmpdir:
            args = SimpleNamespace(
                urls=["https://b23.tv/cMBlJvK"],
                db=os.path.join(tmpdir, "test.db"),
                content_dir=os.path.join(tmpdir, "content"),
                no_transcribe=True,
                whisper_model="small",
                json=False,
            )

            with mock.patch.object(cli, "fetch", side_effect=fake_fetch), \
                 mock.patch.object(cli, "save_result", side_effect=fake_save_result), \
                 mock.patch.object(cli, "VectorDB", FakeDB):
                cli.cmd_ingest(args)

        self.assertFalse(saved["called"])
        self.assertFalse(ingested["called"])


if __name__ == "__main__":
    unittest.main()
