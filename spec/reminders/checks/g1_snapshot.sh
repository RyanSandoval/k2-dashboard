#!/usr/bin/env bash
# G1 — the cron snapshot must emit human reminder text + schedule for reminder-shaped
# jobs, and must NOT attach payload text to ordinary crons.
set -euo pipefail
SNAP=/Users/ryansandoval/.openclaw/workspace/scripts/k2-cron-snapshot.sh
RAW=$(mktemp /tmp/g1_raw_XXXX.json)
OUT=$(mktemp /tmp/g1_out_XXXX.json)
trap 'rm -f "$RAW" "$OUT"' EXIT

/opt/homebrew/bin/openclaw cron list --json --timeout 15000 >"$RAW"

# Extract the jq program from the snapshot script verbatim so this tests the real thing.
PROG=$(sed -n "/^jq '\[.jobs\[\]/,/sort_by(.id)'/p" "$SNAP" | sed "s/^jq '//; s/' \"\$WORK\/raw.json\".*$//")
[ -n "$PROG" ] || { echo "G1 FAIL: could not extract jq program"; exit 1; }
jq "$PROG" "$RAW" >"$OUT"

jq -e '
  (map(select(.isReminder == true))) as $rem |
  (map(select(.isReminder != true))) as $other |
  if ($rem | length) < 5 then error("too few reminders: \($rem|length)")
  elif ($rem | map(select((.reminderText // "") == "")) | length) > 0 then error("reminder with empty text")
  elif ($rem | map(select(.reminderText | test("Output the following"))) | length) > 0 then error("agentTurn boilerplate leaked into reminderText")
  elif ($rem | map(select(.scheduleKind == "at" and .scheduleAt == null)) | length) > 0 then error("one-shot with no scheduleAt")
  elif ($other | map(select(has("reminderText"))) | length) > 0 then error("payload text attached to a non-reminder job")
  elif ($rem | map(select(.reminderOrigin == "asked")) | length) < 1 then error("no asked-origin reminder found")
  else true end' "$OUT" >/dev/null

echo "G1 PASS: $(jq '[.[]|select(.isReminder==true)]|length' "$OUT") reminders, text + schedule present, no boilerplate, non-reminders clean"
