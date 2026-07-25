# Tasks — Commitments-to-Tasks

**Version:** 1.0
**Implements:** requirements.md + design.md
**Rule:** Phase 1 verifies inferences against the real repo BEFORE any new code (retrofit-style). Don't mark `[x]` without meeting the _Verify_ line.

---

## Phase 1 — Verify the ground truth (no new code)

- [ ] **TASK-001 [REQ-003,REQ-004]:** Confirm the Action Inbox scanner's exact form (cron `a6125141`: agentTurn vs script+CLI, where it lives, how it writes) and confirm no existing `DATA.tasks` row already uses `source` / `commitmentKey` keys.
  _Output:_ one-paragraph note in this file under "Findings".
  _Verify:_ scanner form named + a grep of live `data.json` shows zero collisions on `source`/`commitmentKey`.

- [ ] **TASK-002 [REQ-007]:** Confirm `k2_data_set.py` semantics for `tasks`: replacing the key requires passing the FULL merged array; confirm the ARRAY shrink gate (≤50%) won't block a normal week.
  _Output:_ confirmed invocation string.
  _Verify:_ a dry-run `--set tasks=<full current array copy>` round-trips with no gate error (no-op write or `--dry-run` if supported).

- [ ] **TASK-003 [REQ-001,REQ-005]:** Decide Pieces-for-run policy (auto-enable for the weekly scan vs Goldfish-only default). Record decision in design §7.
  _Verify:_ design §7 states the chosen policy; if auto-enable, the enable+reload+disable sequence is written down.

- [ ] **TASK-004 [REQ-006]:** Locate `renderActionInbox` in `index.html` and confirm the task-toggle + `saveData()` handlers the new card will reuse.
  _Verify:_ function names + line refs recorded; no new persistence path needed.

---

## Phase 2 — Scanner (recall → enriched commitments)

- [ ] **TASK-010 [REQ-001,REQ-009]:** Write the bounded recall-pull step (Goldfish `search_memory` on commitment cues + targeted `get_snapshots` limit≤4; Pieces `ask_pieces_ltm`).
  _Output:_ recall step in the scanner prompt/script.
  _Verify:_ a manual run returns ≥1 week's commitments with no token-cap overflow.

- [ ] **TASK-011 [REQ-002,REQ-010]:** Write the extract+enrich step producing the full commitment shape; scrub secrets from `evidence`; flag `unanchored` instead of inventing context.
  _Output:_ enrichment prompt + JSON schema.
  _Verify:_ on the 2026-07-25 sample, every written row has concrete `who`+`specifics`; no token/credential strings in `evidence`; unanchored items are flagged, not written as tasks.

- [ ] **TASK-012 [REQ-004]:** Implement `commitmentKey` (ticket#/subject/normalized-text anchor) + dedupe against live `DATA.tasks` (new / update / respect-done).
  _Output:_ keying + merge logic.
  _Verify:_ run twice on same window ⇒ 0 duplicate tasks; a pre-checked commitment stays done.

- [ ] **TASK-013 [REQ-007]:** Wire the write through `k2_data_set.py` (full merged `tasks` array + `commitmentsMeta`), fail-closed on gate trip.
  _Output:_ write step.
  _Verify:_ successful write updates only `tasks`+`commitmentsMeta`; a forced bad slice is rejected with non-zero exit and no data.json change.

## Phase 3 — Dashboard card

- [ ] **TASK-020 [REQ-006]:** Add `renderCommitments()` to `index.html` — filter `DATA.tasks` by `source==="commitment"`, group by `initiative`, sort by confidence, reuse task checkoff + `saveData()`.
  _Output:_ card + render fn.
  _Verify:_ card shows grouped commitment-tasks with who/next-action/confidence color/source badge; checkoff toggles the same row as the main list.

- [ ] **TASK-021 [REQ-005]:** Confidence + source styling (green/yellow/red dot; goldfish/voice badge) + empty state.
  _Verify:_ voice-only item renders lower-confidence; empty week shows the empty state.

## Phase 4 — Cron + ship

- [ ] **TASK-030 [REQ-001,REQ-008]:** Create the weekly Sunday-AM Sonnet cron via `openclaw cron` CLI (non-blackout, `lightContext:false`), idempotent.
  _Verify:_ `openclaw cron list` shows one weekly job, Sonnet, correct time; a manual trigger completes end-to-end and writes tasks.

- [ ] **TASK-031 [ALL]:** Dry-run one full weekly cycle against the real week; Ryan reviews the resulting commitment-tasks + card before it's left running.
  _Verify:_ Ryan sign-off; dedupe holds on a second run; MEMORY "Active Spec-Driven Projects" updated.

---

## Findings

### Session 2026-07-25 (Phase 1 verified against live repo)
- **TASK-001:** Action Inbox scanner = cron `a6125141` "K2 Action Inbox Scanner", isolated agentTurn, daily `0 2 * * *`, model `anthropic/claude-*`. Live `data.json` = 51 keys, `tasks` = 283 items. **COLLISION: `source` already used on 253/283 tasks** (values: `jot`,`plan-sync`,`ideas-log`,`note`,`jot-mention`,null). ⇒ Do NOT rely on `source` alone as discriminator. `commitmentKey`: **0 collisions**, `commitmentsMeta`: absent. `actionInbox` key present. **Decision:** discriminator = **presence of `commitmentKey`**; also set `source:"commitment"` (fits the existing source taxonomy) but the FILTER keys on `commitmentKey`.
- **TASK-002:** `k2_data_set.py` supports `--dry-run`, `--allow-shrink KEY`, `--set KEY=FILE`, `--message`. Replacing `tasks` = pass FULL merged array (283+N). Normal week won't trip the 50% ARRAY gate. Confirmed invocation: `python3 scripts/k2_data_set.py --set tasks=/tmp/commit-tasks.json --set commitmentsMeta=/tmp/commit-meta.json --message "Commitments sync <ts>"`.
- **TASK-003:** DECIDED — auto-enable Pieces for the run (see design §7).
- **TASK-004:** `renderActionInbox()` @ index.html:3748; badge `renderActionInboxBadge()` @3613; `saveData()` @3267; render registry array @~3351; page routing @3433; list div `#action-inbox-list` @2463. New card mirrors these (delegated).
- **Architecture refinement:** scanner split into (a) LLM recall+enrich → writes enriched JSON to /tmp, (b) deterministic `scripts/commitment_sync.py` that computes `commitmentKey`, dedupes/merges into the live tasks array, writes via `k2_data_set.py`. Keeps fragile merge logic out of the LLM + unit-testable.
