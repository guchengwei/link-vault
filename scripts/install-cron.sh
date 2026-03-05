#!/usr/bin/env bash
# install-cron.sh — Install weekly-push as a cron job (Sundays 3am).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUSH_SCRIPT="$SCRIPT_DIR/weekly-push.sh"
chmod +x "$PUSH_SCRIPT"

CRON_LINE="0 3 * * 0 $PUSH_SCRIPT >> /tmp/linkvault-weekly.log 2>&1"

# Avoid duplicates
(crontab -l 2>/dev/null | grep -v "weekly-push.sh"; echo "$CRON_LINE") | crontab -
echo "Installed cron job: $CRON_LINE"
echo "Log: /tmp/linkvault-weekly.log"
