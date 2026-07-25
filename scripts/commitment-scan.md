# Weekly Commitment Scan — cron runbook / prompt

Canonical prompt for the weekly commitments-to-tasks cron. Keep this file in sync with
the cron `payload.message`. See `spec/commitments-to-tasks/`.

**Schedule:** weekly, Sunday ~09:00 America/Los_Angeles (non-blackout, post sleep-wake bounce).
**Runtime:** isolated agentTurn, model `claude-cli/claude-sonnet-4.6` (claude-cli prefix = full FS + MCP tools; `anthropic/` does NOT get FS tools). `lightContext:false` (needs deferred MCP recall tools).
**Idempotent:** safe to re-run the same week (dedupe guarantees it).
**Create via** `openclaw cron` CLI, NOT the MCP cron tool (it injects toolsAllow and breaks claude-cli jobs).

---

## Prompt (payload.message)

You are the weekly Commitment Scan for Ryan's K2 dashboard. Turn this past week's passive
recall into deduped, checkoffable tasks. Work carefully; never fabricate.

STEP 1 — Enable voice recall (Pieces is dormant by default):
  Run:  `openclaw mcp configure pieces --enable && openclaw mcp reload`
  If this fails, continue Goldfish-only and note "voice coverage OFF" in the summary.

STEP 2 — Pull recall for the trailing 7 days (BOUNDED — never dump full activity):
  - Goldfish: `search_memory` with commitment cues ("follow up", "I'll send", "deliver",
    "by Friday", "next steps", "owe", "action item", ticket/email terms). For the top hits,
    `get_snapshots` on at most 3–4 ids to read the real email/Jira body. Do NOT call
    get_recent_activity (it overflows the token cap).
  - Pieces: `ask_pieces_ltm` question="what commitments/promises did I make this past week?"
    (include audio). Treat voice transcripts as leads, not gospel.

STEP 3 — Extract + enrich. For each genuine commitment produce an object:
  {initiative, commitment, who, specifics, when, nextAction,
   confidence: high|medium|low, sourceLayer: goldfish|pieces-voice|pieces-summary,
   evidence, tickets?: [ "MW-1234" ], emailSubject?: "..." , unanchored?: bool}
  Rules:
  - confidence: email/screen-backed = high; session summary = medium; voice-only = medium/low.
  - Put a ticket number in `tickets` or the subject in `emailSubject` whenever present — this
    is what keeps dedupe stable week to week.
  - If you cannot tie a commitment to a concrete who/what, set "unanchored": true. Do NOT
    invent context. Unanchored items are dropped from tasks (they still show in the summary).
  - SCRUB SECRETS: `evidence` must not contain tokens, API keys, or verify links. Short quote
    or subject only.
  Write the JSON array to `/tmp/commitments-enriched.json`.

STEP 4 — Merge into tasks (deterministic, deduped):
  Run:
    `python3 /Users/ryansandoval/.openclaw/workspace/k2-dashboard/scripts/commitment_sync.py \
       --commitments /tmp/commitments-enriched.json --write \
       --message "Commitments sync $(date +%F)"`
  The script fetches live data.json, computes commitmentKey, appends new / updates open /
  leaves done ones untouched, and writes via the hardened k2_data_set.py. If it exits
  non-zero, STOP — do not retry with a hand-built payload; report the error.

STEP 5 — Always disable Pieces again (even if earlier steps failed):
  Run:  `openclaw mcp configure pieces --disable && openclaw mcp reload`

STEP 6 — Make your FINAL response a short summary (the cron delivers it to #k2-health via
  announce — do NOT call `openclaw message send` yourself, that double-posts). Include:
  counts {new, updated, unanchored}, the initiatives touched, and any "voice coverage OFF"
  note. Keep it under 8 lines. Do not paste secrets.

Order guarantee: run STEP 5 in a finally/always sense — Pieces must return to dormant even
if STEP 2–4 error out.
