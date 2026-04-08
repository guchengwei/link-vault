"""Adapter layer for xfetch CLI ingest/publish and local bundle loading."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from .site_builder import build_site_from_content
from .vectordb import infer_source_type


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


def _normalize_cmd(cmd: str) -> list[str]:
    return cmd.split()


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
    cmd = _normalize_cmd(resolve_xfetch_cmd()) + ["ingest", url, "--json"]
    if content_root:
        cmd.extend(["--content-root", content_root])
    payload = _run_json(cmd)
    if "bundle_path" not in payload and "bundle_dir" in payload:
        payload["bundle_path"] = payload["bundle_dir"]
    payload.setdefault("url", url)
    payload.setdefault("source_type", infer_source_type(url))
    return payload


def _rebuild_target_repo_site(target_repo: str) -> Optional[str]:
    repo_path = Path(target_repo).expanduser()
    if not repo_path.exists() or not repo_path.is_dir():
        return None
    output_paths = build_site_from_content(content_dir=repo_path / "content", site_dir=repo_path / "site")
    homepage = next((path for path in output_paths if path.name == "index.html" and path.parent == repo_path / "site"), None)
    if homepage:
        return str(homepage)
    return str(output_paths[0]) if output_paths else None


def publish_bundle(bundle_path: str) -> Dict[str, Any]:
    target_repo = os.environ.get("XFETCH_TARGET_REPO") or os.environ.get("LINKVAULT_XFETCH_TARGET_REPO")
    repo_owner = os.environ.get("XFETCH_REPO_OWNER") or os.environ.get("LINKVAULT_XFETCH_REPO_OWNER")
    repo_name = os.environ.get("XFETCH_REPO_NAME") or os.environ.get("LINKVAULT_XFETCH_REPO_NAME")
    if not target_repo or not repo_owner or not repo_name:
        raise XFetchError(
            "xfetch publish is not configured. Set XFETCH_TARGET_REPO, XFETCH_REPO_OWNER, and XFETCH_REPO_NAME."
        )
    cmd = _normalize_cmd(resolve_xfetch_cmd()) + [
        "publish",
        bundle_path,
        "--target-repo", target_repo,
        "--repo-owner", repo_owner,
        "--repo-name", repo_name,
        "--json",
    ]
    payload = _run_json(cmd)
    site_build_root = _rebuild_target_repo_site(target_repo)
    if site_build_root:
        payload.setdefault("site_build_root", site_build_root)
    return payload


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
    document = _read_json("document.json")
    if "source_type" not in document:
        document["source_type"] = document.get("kind") or infer_source_type(document.get("url", ""))
    return {
        "bundle_path": str(bundle),
        "document": document,
        "publish": _read_json("publish.json"),
        "index_path": str(index_path) if index_path.exists() else "",
        "index_text": index_path.read_text(encoding="utf-8") if index_path.exists() else "",
    }


def bundle_index_text(bundle_path: str) -> str:
    return load_bundle(bundle_path).get("index_text", "")
