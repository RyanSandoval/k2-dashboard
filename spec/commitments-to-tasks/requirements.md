# Requirements — Commitments-to-Tasks

**Version:** 1.0
**Activated:** 2026-07-25
**Status:** active
**Type:** new feature on existing spec-driven project (k2-dashboard)

---

## Problem

Ryan makes commitments all week — in email, in meetings (voice), on screen — that never reliably become tracked tasks. Goldfish (screen) + Pieces (voice) capture them passively. This feature turns that passive capture into **checkoffable tasks in his existing task list**, contextualized enough to act on, without duplicates on re-runs.

Origin: 2026-07-25 #k2-health. A manual Goldfish+Pieces commitment pull proved the recall works; the first Excel export failed because rows were bare quotes with no who/what/next-action. See [[feedback-commitment-export-needs-context]].

## Goals
- Commitments become real tasks Ryan can check off in the normal task list.
- Each commitment-task is self-contained: what / who's waiting / initiative / specifics / next action.
- Re-running the scan never creates duplicate tasks.
- A grouped dashboard view shows commitment-tasks by initiative with confidence + source.

## Out of scope (v1)
- Auto-drafting replies or auto-acting on commitments (surface only; acting stays manual).
- Real-time capture (weekly batch only).
- Two-way sync back to email/Jira (read-only recall in, tasks out).
- Personal-commitment coaching; personal items are captured but not prioritized.

---

## Functional Requirements

**REQ-001** — The system **shall** run a weekly scan (Sunday morning, outside cron blackout windows) that pulls recall for the trailing 7 days from Goldfish (screen) and Pieces (voice/summary).
_AC:_ A scheduled run produces a timestamped commitment set covering the prior 7 days; `lastScanAt` is stamped.

**REQ-002** — The system **shall** extract commitments and enrich each into the contextualized shape: `initiative, commitment, who, specifics, when, nextAction, confidence, sourceLayer, evidence`.
_AC:_ Given the 2026-07-25 sample data, output rows carry a concrete `who` and `specifics` (ticket # or email subject), not a bare quote. Rows that cannot be anchored to a who/what are flagged `unanchored:true`, never invented.

**REQ-003** — Each anchored commitment **shall** be written as a TASK in `DATA.tasks` (the existing task list), checkoffable in the normal UI, carrying commitment metadata (see design §Data model).
_AC:_ After a run, new commitments appear as tasks in the standard task list with `done:false` and are checkoffable; checking one off persists like any task.

**REQ-004** — The system **shall** dedupe against existing tasks via a stable `commitmentKey` so re-runs update-in-place rather than duplicate.
_AC:_ Running the scan twice on the same window yields the same task count for those commitments (0 duplicates). A commitment whose facts changed updates the existing task's fields; a commitment Ryan already checked off stays done and is not re-opened.

**REQ-005** — Voice-sourced commitments **shall** be marked lower-confidence than screen/email-sourced ones, and confidence **shall** be visible.
_AC:_ A Pieces-voice-only commitment renders yellow/`medium` or `low`; a Goldfish-email-backed one renders green/`high`.

**REQ-006** — The dashboard **shall** render commitment-tasks grouped by initiative, showing who's-waiting, next-action, confidence color, and source layer, with the normal task checkoff.
_AC:_ The card lists the week's commitment-tasks under initiative headers; checking one off there and in the main list are the same action.

**REQ-007** — All writes to `data.json` **shall** go through `scripts/k2_data_set.py` (hardened writer). No LLM-composed full-file PUTs.
_AC:_ The scanner computes only the `tasks` slice (+ meta) into a temp file and calls `k2_data_set.py --set tasks=... --set commitmentsMeta=...`; the run fails closed if a gate trips. See [[feedback-k2-data-json-merge-pattern]].

**REQ-008** — The scan **shall** run on Sonnet (extraction/enrichment), once weekly, never as a high-frequency poller.
_AC:_ Exactly one scheduled job; model is Sonnet; no sub-hourly cadence. See [[feedback-copilot-spend-default-sonnet]], [[project-claude-cli-token-leak-fix]].

**REQ-009** — Recall payloads that overflow the tool token cap (Goldfish `get_recent_activity`, `get_snapshots`) **shall** be handled via low limits + `search_memory` + targeted `get_snapshots`, not by dumping full activity.
_AC:_ No scan step requests an unbounded recall payload; enrichment reads targeted snapshots only. See [[reference-goldfish-mcp]].

**REQ-010** — Recall can surface secrets (OAuth/verify tokens). The system **shall not** persist raw secret-bearing snapshot text into `data.json`.
_AC:_ Stored `evidence` is a short scrubbed quote/subject; no token/credential strings written to the task store.

---

## Clarifications
_(Retrofit-style feature; key decisions taken conversationally 2026-07-25.)_

### Session 2026-07-25
- Q: Cadence? → A: Weekly, Sunday AM (expand to daily only if it earns it).
- Q: Separate card or into task list? → A: Both — real tasks in the existing list AND a grouped commitments view. Not a separate parallel store.
- Q: Sources? → A: Goldfish + Pieces voice (voice flagged lower-confidence).
- Q: Dedupe? → A: Required — stable key; existing task ⇒ update, don't duplicate; respect manual done.
