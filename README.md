# link-vault

xfetch-backed link ingestion and local semantic search.

link-vault now treats `xfetch` as the canonical runtime for ingest, bundle creation, and publish metadata. It indexes local xfetch bundle content, primarily `index.md`, into a local SQLite vector database for semantic search.

## What it does

- ingest URLs through xfetch
- publish saved bundles automatically through xfetch's configured target workflow
- allow partial success when local ingest succeeds but publish fails
- index local bundle markdown for semantic search
- keep local document metadata, bundle paths, and publish status in SQLite

## Quickstart

```bash
python -m linkvault ingest https://example.com/article
python -m linkvault ingest https://example.com/article https://example.com/post
python -m linkvault search "machine learning"
python -m linkvault list
python -m linkvault stats
```

## /save behavior

`/save <url>` should run:

```bash
cd /home/nvidia/.openclaw/workspace/link-vault && python3 -m linkvault --db /home/nvidia/.openclaw/workspace/link-vault/linkvault.db --content-dir /home/nvidia/.openclaw/workspace/link-vault/content --json ingest "<url>"
```

Response semantics:

- `Saved + published: <title> -> <public_url>`
- `Saved locally, publish failed: <title> -> <publish_error>`
- `Save failed: <url> -> <error>`

## Architecture

```text
Any URL -> xfetch ingest -> local bundle (document.json + index.md + publish metadata)
                        -> xfetch publish
                        -> link-vault indexes index.md into SQLite vectors
```

### Canonical responsibilities

- `xfetch` owns ingest
- `xfetch` owns local bundle creation
- `xfetch` owns render output and publish metadata
- `xfetch` owns sync/publish into the target content repo
- `link-vault` owns local semantic indexing and search over saved bundles

## Publish target

Publish follows xfetch settings and is intended to target:

- repo: `guchengwei/link-vault`
- serving model: GitHub Pages from that repo

link-vault should not invent a separate publish destination.

## Search model

- primary indexed body: bundle `index.md`
- document metadata source: bundle `document.json`
- stored metadata: local bundle path, index path, public URL, publish status

## Current repository shape

```text
link-vault/
├── linkvault/
│   ├── cli.py
│   ├── mcp_server.py
│   ├── vectordb.py
│   └── xfetch_adapter.py
├── tests/
│   ├── fixtures/xfetch/
│   ├── test_smoke.py
│   └── test_mcp_tools.py
└── README.md
```

## Environment

The xfetch CLI must be available on PATH, or configured via one of:

- `XFETCH_CMD`
- `LINKVAULT_XFETCH_CMD`

For publish to work end to end, configure:

- `XFETCH_TARGET_REPO`
- `XFETCH_REPO_OWNER`
- `XFETCH_REPO_NAME`

Example:

```bash
export XFETCH_CMD='python3 -m xfetch'
export XFETCH_TARGET_REPO='/home/nvidia/.openclaw/workspace/link-vault-publish'
export XFETCH_REPO_OWNER='guchengwei'
export XFETCH_REPO_NAME='link-vault'
```

## Validation

Validated with a real end-to-end run after installing xfetch locally:

- local ingest through xfetch
- local indexing of bundle `index.md`
- real publish to `guchengwei/link-vault`
- resulting public URL, for example:
  - <https://guchengwei.github.io/link-vault/d/web-ef3f409f8927-example-com/>

## Notes

- old fetch/storage pipeline components should be removed from active runtime use
- old weekly push scripts are obsolete once publish happens during ingest
- transcription remains a separate review area until xfetch capability is confirmed
