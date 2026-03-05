#!/usr/bin/env bash
# weekly-push.sh — Commit new content and push to GitHub.
# Intended for cron: 0 3 * * 0 /path/to/weekly-push.sh
#
# What it does:
#   1. cd to the link-vault repo
#   2. Stage all new/changed content/ files and the database
#   3. Commit with a dated message
#   4. Push to origin
#
# Exit codes: 0 = pushed (or nothing to push), 1 = error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

cd "$REPO_DIR"

# Check for changes
if git diff --quiet HEAD -- content/ linkvault.db 2>/dev/null && \
   [ -z "$(git ls-files --others --exclude-standard content/)" ]; then
    echo "[weekly-push] No new content to push."
    exit 0
fi

WEEK=$(date +%Y-W%V)
git add content/ linkvault.db 2>/dev/null || true
git commit -m "content: weekly sync ${WEEK}

Auto-committed by weekly-push.sh" || { echo "[weekly-push] Nothing to commit."; exit 0; }

git push origin HEAD 2>&1
echo "[weekly-push] Pushed content for ${WEEK}."
