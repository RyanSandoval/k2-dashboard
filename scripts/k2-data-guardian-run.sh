#!/usr/bin/env bash
# launchd runner for the k2-data guardian. Runs the deterministic guardian,
# logs every cycle, and alerts #k2-dashboard only when it RESTORES a wipe or
# hits an ERROR. Healing is fully LLM-free; alerting uses the openclaw CLI.
set -uo pipefail

export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
DIR="/Users/ryansandoval/.openclaw/workspace/k2-dashboard"
GUARDIAN="$DIR/scripts/k2-data-guardian.sh"
LOG="$DIR/logs/k2-data-guardian.log"
CH="channel:1476441453394919587"   # #k2-dashboard
OPENCLAW="/opt/homebrew/bin/openclaw"

mkdir -p "$DIR/logs"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LINE="$(bash "$GUARDIAN" 2>>"$LOG")"
echo "$TS $LINE" >> "$LOG"

case "$LINE" in
  *RESTORED*)
    "$OPENCLAW" message send --channel discord --target "$CH" \
      --message "🛡️ **K2 Data Guardian — AUTO-RESTORE** ($TS)
data.json was wiped and has been automatically restored from git history.
\`${LINE#GUARDIAN_RESULT: }\`
Check which cron wrote the wipe (Floating Decision / Action Inbox scanners are the known offenders)." >/dev/null 2>&1
    ;;
  *ERROR*)
    "$OPENCLAW" message send --channel discord --target "$CH" \
      --message "⚠️ **K2 Data Guardian — ERROR** ($TS)
\`${LINE#GUARDIAN_RESULT: }\`
data.json may be wiped and the guardian could NOT auto-restore. Manual check needed." >/dev/null 2>&1
    ;;
esac
