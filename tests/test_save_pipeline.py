import json
import os
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIXTURE_BUNDLE = Path(__file__).parent / "fixtures" / "xfetch" / "example-bundle"


class FakeDB:
    def __init__(self, path):
        self.path = path

    def ingest(self, **kwargs):
        raise ModuleNotFoundError("No module named 'transformers'")

    def close(self):
        pass


class _FakeMCP:
    def __init__(self, *args, **kwargs):
        pass

    def tool(self, fn):
        return fn

    def run(self):
        return None


def _load_mcp_server_module():
    sys.modules.setdefault("fastmcp", types.SimpleNamespace(FastMCP=_FakeMCP))
    sys.modules.pop("linkvault.mcp_server", None)
    import linkvault.mcp_server as mcp_server

    return mcp_server


def test_cli_ingest_index_failure_does_not_fail_save(capsys):
    from linkvault import cli

    with tempfile.TemporaryDirectory() as tmpdir:
        args = type(
            "Args",
            (),
            {
                "urls": ["https://example.com/test-article"],
                "db": str(Path(tmpdir) / "cli.db"),
                "content_dir": tmpdir,
                "json": True,
            },
        )
        with mock.patch("linkvault.cli.VectorDB", FakeDB), mock.patch(
            "linkvault.cli.ingest_url",
            return_value={"url": "https://example.com/test-article", "bundle_path": str(FIXTURE_BUNDLE)},
        ), mock.patch(
            "linkvault.cli.publish_bundle",
            return_value={"ok": True, "public_url": "https://example.com/public"},
        ):
            cli.cmd_ingest(args)

    data = json.loads(capsys.readouterr().out)
    assert data[0]["ok"] is True
    assert data[0]["published"] is True
    assert data[0]["index_status"] == "failed"
    assert "transformers" in data[0]["index_error"]


def test_mcp_ingest_index_failure_does_not_fail_save():
    mcp_server = _load_mcp_server_module()

    with tempfile.TemporaryDirectory() as tmpdir:
        with mock.patch("linkvault.mcp_server.VectorDB", FakeDB), mock.patch(
            "linkvault.mcp_server.ingest_url",
            return_value={"url": "https://example.com/test-article", "bundle_path": str(FIXTURE_BUNDLE)},
        ), mock.patch(
            "linkvault.mcp_server.publish_bundle",
            return_value={"ok": True, "public_url": "https://example.com/public"},
        ):
            result = mcp_server._ingest(["https://example.com/test-article"], db_path=str(Path(tmpdir) / "mcp.db"), content_dir=tmpdir)

    row = result["results"][0]
    assert row["error"] is None
    assert row["published"] is True
    assert row["index_status"] == "failed"
    assert "transformers" in row["index_error"]
