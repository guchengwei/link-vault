import os
from pathlib import Path
from unittest import mock

import pytest

from linkvault.xfetch_adapter import publish_bundle


@pytest.fixture
def publish_env(tmp_path):
    env = {
        "XFETCH_TARGET_REPO": str(tmp_path / "publish-repo"),
        "XFETCH_REPO_OWNER": "guchengwei",
        "XFETCH_REPO_NAME": "link-vault",
    }
    with mock.patch.dict(os.environ, env, clear=False):
        yield env


def test_publish_bundle_refreshes_homepage_for_local_target_repo(publish_env):
    repo_path = Path(publish_env["XFETCH_TARGET_REPO"])
    repo_path.mkdir(parents=True)

    with mock.patch("linkvault.xfetch_adapter.resolve_xfetch_cmd", return_value="xfetch"), \
         mock.patch("linkvault.xfetch_adapter._run_json", return_value={"ok": True, "public_url": "https://example.com/published"}) as run_json, \
         mock.patch("linkvault.xfetch_adapter.build_homepage_index", return_value=repo_path / "site" / "index.html") as build_index:
        payload = publish_bundle("/tmp/bundle")

    run_json.assert_called_once_with(
        [
            "xfetch",
            "publish",
            "/tmp/bundle",
            "--target-repo",
            str(repo_path),
            "--repo-owner",
            "guchengwei",
            "--repo-name",
            "link-vault",
            "--json",
        ]
    )
    build_index.assert_called_once_with(content_dir=repo_path / "content", site_dir=repo_path / "site")
    assert payload["homepage_index"] == str(repo_path / "site" / "index.html")


def test_publish_bundle_skips_homepage_refresh_for_nonlocal_target_repo():
    env = {
        "XFETCH_TARGET_REPO": "guchengwei/link-vault",
        "XFETCH_REPO_OWNER": "guchengwei",
        "XFETCH_REPO_NAME": "link-vault",
    }
    with mock.patch.dict(os.environ, env, clear=False), \
         mock.patch("linkvault.xfetch_adapter.resolve_xfetch_cmd", return_value="xfetch"), \
         mock.patch("linkvault.xfetch_adapter._run_json", return_value={"ok": True, "public_url": "https://example.com/published"}), \
         mock.patch("linkvault.xfetch_adapter.build_homepage_index") as build_index:
        payload = publish_bundle("/tmp/bundle")

    build_index.assert_not_called()
    assert "homepage_index" not in payload
