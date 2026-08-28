#!/usr/bin/env bash
# G1 — the cron snapshot must emit human reminder text + note + schedule for
# reminder-shaped jobs, and must NOT attach payload text to ordinary crons.
#
# This runs the REAL script via --emit. An earlier version of this gate scraped the jq
# program out with sed and ran that instead, so it could not see a shell-quoting break
# in the script itself — and did not, when an apostrophe in a jq comment froze the live
# snapshot. Test the artifact, not a copy of part of it.
set -euo pipefail
SNAP=/Users/ryansandoval/.openclaw/workspace/scripts/k2-cron-snapshot.sh
OUT=$(mktemp /tmp/g1_out_XXXX.json)
trap 'rm -f "$OUT"' EXIT

bash "$SNAP" --emit >"$OUT"

jq -e '
  (map(select(.isReminder == true))) as $rem |
  (map(select(.isReminder != true))) as $other |
  if ($rem | length) < 5 then error("too few reminders: \($rem|length)")
  elif ($rem | map(select((.reminderText // "") == "")) | length) > 0 then error("reminder with empty text")
  elif ($rem | map(select(.reminderText | test("Output the following"))) | length) > 0 then error("agentTurn boilerplate leaked into reminderText")
  elif ($rem | map(select(.scheduleKind == "at" and .scheduleAt == null)) | length) > 0 then error("one-shot with no scheduleAt")
  elif ($other | map(select(has("reminderText"))) | length) > 0 then error("payload text attached to a non-reminder job")
  elif ($rem | map(select(has("reminderNote") | not)) | length) > 0 then error("reminder missing the reminderNote field")
  else true end' "$OUT" >/dev/null

echo "G1 PASS: $(jq '[.[]|select(.isReminder==true)]|length' "$OUT") reminders via the real script (--emit), text+note+schedule present, non-reminders clean"
