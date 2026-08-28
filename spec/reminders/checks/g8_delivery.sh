#!/usr/bin/env bash
# G8 — remind_fire.sh must hit BOTH channels, and neither may be able to suppress the
# other. Runs the real script against stubs so no test message reaches Discord.
set -uo pipefail
WRAP=/Users/ryansandoval/.openclaw/workspace/scripts/remind_fire.sh
W=$(mktemp -d /tmp/g8_XXXX); trap 'rm -rf "$W"' EXIT
FAIL=0
note() { echo "  $1"; FAIL=1; }

mk_stub() { printf '#!/bin/sh\necho "$@" >> %s\nexit %s\n' "$2" "$3" > "$1"; chmod +x "$1"; }

# --- both channels healthy ---
mk_stub "$W/oc" "$W/discord.log" 0
mk_stub "$W/push" "$W/push.log" 0
OPENCLAW_BIN="$W/oc" WEBPUSH_BIN="$W/push" PYTHON_BIN=/bin/sh \
  "$WRAP" --target channel:123 --message "⏰ Reminder: call the dentist
ask about the crown" >/dev/null 2>&1
rc=$?
[ "$rc" -eq 0 ] || note "healthy path exited $rc, want 0"
grep -q "message send --target channel:123" "$W/discord.log" 2>/dev/null || note "discord leg not called with the target"
grep -q "call the dentist" "$W/discord.log" 2>/dev/null || note "discord leg lost the reminder text"
grep -q -- "--send ⏰ Reminder" "$W/push.log" 2>/dev/null || note "push leg not called"
grep -q "call the dentist" "$W/push.log" 2>/dev/null || note "push leg lost the reminder text"
grep -q "⏰ Reminder: call the dentist" "$W/push.log" 2>/dev/null && note "push body still carries the Discord prefix"
grep -q "ask about the crown" "$W/push.log" 2>/dev/null || note "push leg dropped the note"

# --- push down: the reminder must still be delivered and the run must not fail ---
: > "$W/discord.log"; mk_stub "$W/push" "$W/push.log" 1
OPENCLAW_BIN="$W/oc" WEBPUSH_BIN="$W/push" PYTHON_BIN=/bin/sh \
  "$WRAP" --target channel:123 --message "x" >/dev/null 2>&1
[ "$?" -eq 0 ] || note "a push failure failed the whole reminder"
grep -q "channel:123" "$W/discord.log" 2>/dev/null || note "push failure suppressed the discord post"

# --- discord down: push must still fire, and the run must report failure ---
: > "$W/push.log"; mk_stub "$W/oc" "$W/discord.log" 1; mk_stub "$W/push" "$W/push.log" 0
OPENCLAW_BIN="$W/oc" WEBPUSH_BIN="$W/push" PYTHON_BIN=/bin/sh \
  "$WRAP" --target channel:123 --message "y" >/dev/null 2>&1
[ "$?" -ne 0 ] || note "a discord failure was reported as success"
grep -q -- "--send" "$W/push.log" 2>/dev/null || note "discord failure suppressed the push"

# --- bad input must be rejected, not half-sent ---
OPENCLAW_BIN="$W/oc" WEBPUSH_BIN="$W/push" PYTHON_BIN=/bin/sh "$WRAP" --message "no target" >/dev/null 2>&1
[ "$?" -eq 2 ] || note "missing --target was not rejected"

[ "$FAIL" -eq 0 ] || { echo "G8 FAIL:"; exit 1; }
echo "G8 PASS: both channels fire; push failure never costs the reminder; discord failure still reports"
