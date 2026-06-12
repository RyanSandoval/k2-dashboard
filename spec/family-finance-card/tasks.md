🏛️ family-finance-card

# Tasks — K2 Family Finance Snapshot Card

**Version:** v0.1
Order: emitter (family-finance) → cron (writer) → UI (reader). Build top to bottom.

---

## Phase 1 — Family-Finance Side

- [ ] **TASK-001 [REQ-026 of family-finance]** Add `src/skills/k2-snapshot.ts`
  - Pure `buildK2Snapshot(opts?)`: reads store, current-month txs, accounts, budgets; returns the snapshot per [[design.md]].
  - Reuses existing helpers: `loadTransactionsInRange`, accounts from `state.json`, `computeBudgetVariance` (where useful).
  - Excludes Transfers/Investments/Income/Rewards from "discretionary" buckets used by burn + topCategory.
  - **Verify:** unit test on a fixture (3 categories + 2 days of txs) — assert snapshot fields all populated and within ±$0.01 of hand-calc.

- [ ] **TASK-002 [REQ-026]** Add CLI wrapper `src/k2-snapshot.ts` + `package.json` script `emit:k2-snapshot`
  - `node dist/k2-snapshot.js` outputs a single JSON line to stdout, exit 0 on success.
  - Errors go to stderr; non-zero exit on store missing or 0 accounts.
  - **Verify:** `cd family-finance && npm run build && npm run emit:k2-snapshot | jq '.netPosition.mtdNet'` returns a number.

- [ ] **TASK-003 [REQ-026 + REQ-N05]** Stale-handling
  - When the most recent SimpleFIN `last_synced_at` is >24h ago, set `freshness.stale: true` and emit best-effort numeric fields anyway (the writer cron decides how the UI renders).
  - **Verify:** force `state.json.accounts[*].last_synced_at` back 30h in a fixture; emitter still outputs valid JSON with `stale: true`.

- [ ] **TASK-004** Append REQ-026 to `family-finance/requirements.md` and TASK-034 to `family-finance/tasks.md`
  - REQ-026: "System shall emit a compact K2 dashboard snapshot via `src/skills/k2-snapshot.ts` containing net position MTD, burn rate, top category, and freshness — no raw accounts or transactions."
  - TASK-034: "Cron-callable JSON emitter for K2 dashboard snapshot card."
  - **Verify:** `grep REQ-026 family-finance/requirements.md` returns the line.

## Phase 2 — OpenClaw Cron

- [ ] **TASK-005 [REQ-007, REQ-008, REQ-009, NFR-1, NFR-2]** Create cron "K2 Family Finance Snapshot"
  - Schedule: every 2h during work hours, off the :00/:30 mark
  - isolated, lightContext, haiku, 180s timeout
  - Bash:
    1. `cd ~/.openclaw/workspace/family-finance && npm run emit:k2-snapshot > /tmp/k2_ff.json 2> /tmp/k2_ff_err.log`
    2. Validate `/tmp/k2_ff.json` parses + has `netPosition` + `burnRate` + `topCategory` + `freshness` keys.
    3. File-based GET data.json → `/tmp/k2_resp.json` → `/tmp/k2_full.json`.
    4. Safety gates B/C/D (existing has ≥5 non-target keys, key set unchanged after merge, size not halved).
    5. jq merge: `.familyFinanceSnapshot = <emitter output> | .familyFinanceSnapshotMeta = {writtenAt:NOW, source:"k2-family-finance-snapshot-cron"}`.
    6. File-based PUT.
  - **Verify:** Force-run → `data.json` has both new keys, all other keys intact, size delta < +3KB.

## Phase 3 — K2 Dashboard UI

- [ ] **TASK-006 [REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-008, NFR-3, NFR-4]** Add card to dashboard
  - Identify the existing Dashboard render fn (likely `renderDashboard()` or `renderHome()` per [INFERRED] in [[design.md]]).
  - Insert HTML container `<div id="dashboard-family-finance-card">`.
  - New `renderFamilyFinanceCard()`:
    - Reads `DATA.familyFinanceSnapshot`; silently no-op if missing (NFR-3).
    - Renders 4 rows: net position, burn rate (with tri-color), top category, freshness.
    - Stale handling: dim numbers, grey burn status, italic "data stale" note.
  - Call from the dashboard render fn.
  - **Verify:** Local refresh after a successful cron run shows all 3 metrics; force a stale state and verify the dim+chip behavior.

- [ ] **TASK-007 [REQ-006]** "Run daily brief →" affordance
  - Button below the snapshot rows.
  - `onclick=_copyFFDailyBriefPrompt()` → copies `@K2 fire family-finance daily check-in` to clipboard + showToast confirming.
  - **Verify:** Click in the UI, paste in #financial channel, K-2 fires the existing skill.

## Phase 4 — Ship

- [ ] **TASK-008** Commit + push `k2-dashboard/index.html` + `spec/family-finance-card/` + family-finance changes.
  - Two repos: k2-dashboard (UI + spec) + family-finance is local but gitignored data — only TS source needs the commit.
  - **Verify:** k2-dashboard remote HEAD shows the commit; family-finance `npm test` passes including the new k2-snapshot test.

- [ ] **TASK-009** Update workspace `MEMORY.md` Active Spec-Driven Projects with this spec's path.
  - **Verify:** Line present in MEMORY.md.
