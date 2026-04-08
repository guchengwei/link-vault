"""Adapter layer for xfetch CLI ingest/publish and local bundle loading."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


class XFetchError(RuntimeError):
    pass


_ENV_KEYS = (
    "XFETCH_CMD",
    "LINKVAULT_XFETCH_CMD",
)


def resolve_xfetch_cmd() -> str:
    for key in _ENV_KEYS:
        value = os.environ.get(key)
        if value:
            return value
    found = shutil.which("xfetch")
    if found:
        return found
    raise XFetchError(
        "xfetch CLI not found. Set XFETCH_CMD or LINKVAULT_XFETCH_CMD, or install xfetch."
    )


def _run_json(args: list[str], cwd: Optional[str] = None) -> Dict[str, Any]:
    proc = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    payload = None
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise XFetchError(f"Invalid JSON from {' '.join(args)}: {stdout[:400]}") from exc
    if proc.returncode != 0:
        detail = payload.get("error") if isinstance(payload, dict) else stderr or stdout
        raise XFetchError(detail or f"xfetch command failed with exit code {proc.returncode}")
    if payload is None:
        raise XFetchError(f"No JSON output from {' '.join(args)}")
    return payload


def ingest_url(url: str, content_root: Optional[str] = None) -> Dict[str, Any]:
    cmd = [resolve_xfetch_cmd(), "ingest", "--json", url]
    if content_root:
        cmd.extend(["--content-root", content_root])
    return _run_json(cmd)


def publish_bundle(bundle_path: str) -> Dict[str, Any]:
    cmd = [resolve_xfetch_cmd(), "publish", "--json", bundle_path]
    return _run_json(cmd)


def load_bundle(bundle_path: str) -> Dict[str, Any]:
    bundle = Path(bundle_path)
    if not bundle.exists():
        raise XFetchError(f"Bundle path does not exist: {bundle_path}")

    def _read_json(name: str) -> Dict[str, Any]:
        path = bundle / name
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    index_path = bundle / "index.md"
    return {
        "bundle_path": str(bundle),
        "document": _read_json("document.json"),
        "publish": _read_json("publish.json"),
        "index_path": str(index_path) if index_path.exists() else "",
        "index_text": index_path.read_text(encoding="utf-8") if index_path.exists() else "",
    }


def bundle_index_text(bundle_path: str) -> str:
    return load_bundle(bundle_path).get("index_text", "")
