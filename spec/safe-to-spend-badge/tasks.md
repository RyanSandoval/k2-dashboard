🏛️ safe-to-spend-badge

# Tasks — SafeToSpend Reality-Corrected Finance Badge

**Version:** v0.1 (2026-06-20)

## Phase 1 — family-finance emitter

- [ ] **TASK-001 [REQ-006]:** Create `family-finance/data/fixed-costs.json` seeded with `merchantMatch:"Bilt Eqr Web Pay"`, `expectedMonthly:3174`, `overrideMonthly:null`, `detectFromTransactions:true`, `includeCcMinimums:true`, `includeAutoLoan:true`, `redThresholdPct:20`.
  - _Output:_ valid JSON file.
  - _Verify:_ `node -e "JSON.parse(require('fs').readFileSync('family-finance/data/fixed-costs.json'))"` exits 0.

- [ ] **TASK-002 [REQ-001..005,007,010]:** Extend `src/skills/k2-snapshot.ts` — add `FixedCostsConfig` type, `safeToSpend?` to `FamilyFinanceK2Snapshot`, `resolveRent()` helper, and the block computation gated on a new optional `fixedCosts` opt + try/catch around `computeSafeToSpend`.
  - _Output:_ compiles; block omitted when opt absent or forecaster throws.
  - _Verify:_ `npm run build` (tsc) succeeds with no errors.

- [ ] **TASK-003 [REQ-006,010]:** Update CLI wrapper `src/k2-snapshot.ts` to read `data/fixed-costs.json` and pass it as `fixedCosts`; missing/invalid file → `undefined` (no crash).
  - _Output:_ wrapper passes config through.
  - _Verify:_ `npm run build` succeeds.

- [ ] **TASK-004 [REQ-001..005]:** Run the emitter against live data, inspect the `safeToSpend` block.
  - _Verify:_ `npm run emit:k2-snapshot` prints JSON where `ccMinimums===885`, `autoLoan===1042`, `rentSource==="observed"`, `rent≈3174`, and `corrected===round2(raw-total)`.

## Phase 2 — k2-dashboard render

- [ ] **TASK-005 [REQ-008,009]:** Add the badge block to `renderFamilyFinanceCard()` in `k2-dashboard/index.html` — corrected headline, de-emphasized raw + delta chip, breakdown line; `if (sts)` guard; stale dimming + red-suppression.
  - _Output:_ badge HTML inserted under the card header.
  - _Verify:_ render the dashboard locally with a snapshot containing `safeToSpend`; badge shows all four elements.

## Phase 3 — verify + ship

- [ ] **TASK-006 [REQ-008,009]:** Render dashboard at desktop (≈1280) and mobile (375×667), screenshot both. Confirm corrected is dominant, raw struck-through, chip + breakdown legible, no layout break, card unchanged when `safeToSpend` absent.
  - _Verify:_ two screenshots reviewed.

- [ ] **TASK-007:** Rebuild family-finance `dist/`, commit + push both repos (family-finance + k2-dashboard).
  - _Verify:_ `git log` shows both commits; `dist/skills/k2-snapshot.js` contains the new logic.

- [ ] **TASK-008:** Trigger the **K2 Family Finance Snapshot** cron to populate `DATA.familyFinanceSnapshot.safeToSpend`; confirm GitHub Pages serves the new field and the live badge renders.
  - _Verify:_ live data.json has `safeToSpend`; hard-refreshed dashboard shows the badge.

- [ ] **TASK-009:** Append the project to MEMORY.md "Active Spec-Driven Projects" and mark this tasks.md complete.
