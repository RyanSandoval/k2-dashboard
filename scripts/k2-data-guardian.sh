#!/usr/bin/env bash
# K2 data guardian — deterministic backstop against silent data.json wipes.
# Any k2-data writer (cron or otherwise) that nukes/truncates data.json gets
# auto-healed here within one guardian cycle. This script NEVER touches a
# healthy file; it only writes when data.json is already wiped, and only ever
# writes a validated healthy blob pulled from git history. Zero risk of the
# guardian itself causing harm.
#
# Exit is always 0 so the caller's relay logic can parse the single
# GUARDIAN_RESULT: line regardless of outcome.
set -uo pipefail

REPO="RyanSandoval/k2-data"
FILE="data.json"
MIN_BYTES=100000   # healthy real file is ~595KB; wiped states seen were 0/257/8510
MIN_KEYS=20        # healthy file has ~50 top-level keys

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

result() { echo "GUARDIAN_RESULT: $*"; exit 0; }

command -v gh >/dev/null 2>&1 || result "ERROR gh CLI not found"
command -v jq >/dev/null 2>&1 || result "ERROR jq not found"

# Fetch the live file into $1. Echoes one line: "<state> <bytes> <keys>" where
# state is ok|wiped|transient. Distinguishes a genuine wipe (valid API
# response, small-but-parseable or 0-byte content) from a transient fetch
# failure (bad API response) — only the former is ever acted on, so a network
# blip can never trigger a spurious restore. Runs in a subshell (command
# substitution), so it must not rely on setting globals.
probe() {
  local out="$1" resp="$TMP/resp.json" b k
  if ! gh api "repos/$REPO/contents/$FILE" > "$resp" 2>/dev/null; then
    echo "transient 0 0"; return
  fi
  if ! jq -e 'has("content") and has("sha")' "$resp" >/dev/null 2>&1; then
    echo "transient 0 0"; return
  fi
  jq -r '.content' "$resp" | base64 -d > "$out" 2>/dev/null || { echo "transient 0 0"; return; }
  b=$(wc -c < "$out" | tr -d ' ')
  k=$(jq 'keys|length' "$out" 2>/dev/null || true); k=${k:-0}
  if [ "$b" -ge "$MIN_BYTES" ] && [ "$k" -ge "$MIN_KEYS" ]; then
    echo "ok $b $k"
  else
    echo "wiped $b $k"
  fi
}

# --- first probe ---
read -r STATUS BYTES KEYS < <(probe "$TMP/cur.json")
[ "$STATUS" = "transient" ] && result "SKIP transient fetch error — no action taken"
[ "$STATUS" = "ok" ] && result "HEALTHY bytes=$BYTES keys=$KEYS"

# --- re-confirm the wipe once before acting (kills transient false positives) ---
FIRST_BYTES=$BYTES
sleep 3
read -r STATUS BYTES KEYS < <(probe "$TMP/cur.json")
[ "$STATUS" = "transient" ] && result "SKIP wipe unconfirmed (transient on recheck) — no action"
[ "$STATUS" = "ok" ] && result "HEALTHY on recheck bytes=$BYTES keys=$KEYS (first probe read ${FIRST_BYTES}B — transient)"

# --- WIPE confirmed twice: find most recent healthy commit ---
echo "guardian: wipe confirmed (bytes=$BYTES keys=$KEYS) — searching last-good commit" >&2
COMMITS=$(gh api "repos/$REPO/commits?path=$FILE&per_page=50" --jq '.[].sha' 2>/dev/null || true)
[ -n "$COMMITS" ] || result "ERROR wipe detected (bytes=$BYTES) but commit history fetch failed"

GOOD=""
for sha in $COMMITS; do
  sz=$(gh api "repos/$REPO/contents/$FILE?ref=$sha" --jq '.size' 2>/dev/null || echo 0)
  if [ "${sz:-0}" -ge "$MIN_BYTES" ]; then GOOD="$sha"; break; fi
done
[ -n "$GOOD" ] || result "ERROR wipe detected (bytes=$BYTES) but no healthy commit in last 50"

# --- pull + validate the good blob before trusting it ---
gh api "repos/$REPO/contents/$FILE?ref=$GOOD" --jq '.content' 2>/dev/null \
  | base64 -d > "$TMP/good.json" 2>/dev/null || result "ERROR could not fetch good commit $GOOD"
GBYTES=$(wc -c < "$TMP/good.json" | tr -d ' ')
GKEYS=$(jq 'keys|length' "$TMP/good.json" 2>/dev/null || echo 0)
if [ "$GBYTES" -lt "$MIN_BYTES" ] || [ "$GKEYS" -lt "$MIN_KEYS" ]; then
  result "ERROR chosen good commit ${GOOD:0:8} failed validation (bytes=$GBYTES keys=$GKEYS)"
fi
jq empty "$TMP/good.json" 2>/dev/null || result "ERROR good commit ${GOOD:0:8} is not valid JSON"

# --- restore: PUT the validated blob from a file (never through a bash var) ---
base64 < "$TMP/good.json" | tr -d '\n' > "$TMP/good.b64"
CUR_SHA=$(gh api "repos/$REPO/contents/$FILE" --jq '.sha' 2>/dev/null | tr -d '"')
[ -n "$CUR_SHA" ] || result "ERROR could not read current sha for restore PUT"
jq -n \
  --arg m "guardian: auto-restore $FILE from ${GOOD:0:8} (wipe detected: was ${BYTES}B/${KEYS} keys)" \
  --rawfile c "$TMP/good.b64" \
  --arg s "$CUR_SHA" \
  '{message:$m, content:$c, sha:$s}' > "$TMP/put.json"

if gh api -X PUT "repos/$REPO/contents/$FILE" --input "$TMP/put.json" >/dev/null 2>&1; then
  result "RESTORED from=${GOOD:0:8} restored_bytes=$GBYTES restored_keys=$GKEYS was_bytes=$BYTES was_keys=$KEYS"
else
  result "ERROR restore PUT failed (validated good commit was ${GOOD:0:8})"
fi
