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


def test_publish_bundle_delegates_to_xfetch(publish_env):
    repo_path = Path(publish_env["XFETCH_TARGET_REPO"])
    repo_path.mkdir(parents=True)
    expected = {"ok": True, "public_url": "https://example.com/published"}

    with mock.patch("linkvault.xfetch_adapter.resolve_xfetch_cmd", return_value="xfetch"), \
         mock.patch("linkvault.xfetch_adapter._run_json", return_value=expected) as run_json:
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
    assert payload == expected
