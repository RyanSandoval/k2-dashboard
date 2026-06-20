🏛️ safe-to-spend-badge

# Design — SafeToSpend Reality-Corrected Finance Badge

**Version:** v0.1 (2026-06-20)

## Overview

Two changes across two repos:

1. **family-finance** — extend the K2 snapshot emitter to compute and emit a `safeToSpend` block, driven by a new editable `data/fixed-costs.json`.
2. **k2-dashboard** — render that block as a badge at the top of the existing 💰 Family Finance card.

No new cron, no new data plumbing: the existing **K2 Family Finance Snapshot** cron (REQ-007 of [[family-finance-card]]) already runs the emitter and jq-merges its JSON into `DATA.familyFinanceSnapshot`. The new field rides along automatically once the emitter is rebuilt and deployed.

```
[fixed-costs.json] ─┐
[debts.json] ───────┤
[state/manual accts]├─► buildK2Snapshot() ─► {...existing, safeToSpend} ─► cron jq-merge ─► DATA.familyFinanceSnapshot ─► renderFamilyFinanceCard()
[transactions.jsonl]┤                                                                                                        (badge)
[patterns.json] ────┘  (computeSafeToSpend)
```

## Data model

### New file: `family-finance/data/fixed-costs.json`
```json
{
  "rent": {
    "merchantMatch": "Bilt Eqr Web Pay",
    "expectedMonthly": 3174,
    "overrideMonthly": null,
    "detectFromTransactions": true
  },
  "includeCcMinimums": true,
  "includeAutoLoan": true,
  "redThresholdPct": 20
}
```
Loaded by the CLI wrapper `src/k2-snapshot.ts` and passed into `buildK2Snapshot`. Missing file → safe defaults (all-on, threshold 20, rent expected 0 so rent contributes nothing until configured — but file ships seeded).

### Emitted shape (added to `FamilyFinanceK2Snapshot`)
```ts
safeToSpend?: {
  raw: number;            // computeSafeToSpend(...).safe_to_spend
  corrected: number;      // round2(raw - fixedCostsOmitted.total)
  deltaPct: number;       // round2(total / raw * 100) when raw > 0 else 0
  fixedCostsOmitted: {
    rent: number;
    ccMinimums: number;
    autoLoan: number;
    total: number;
  };
  rentSource: "override" | "observed" | "config";
  redThresholdPct: number;
};
```
Optional (`?`): omitted entirely when `raw` can't be computed (REQ-010).

## Key components

### `buildK2Snapshot` (family-finance/src/skills/k2-snapshot.ts)
- New optional opt: `fixedCosts?: FixedCostsConfig`. When absent, `safeToSpend` is skipped (keeps unit tests that don't pass it unaffected).
- Steps:
  1. `patterns = await store.loadPatterns()`; `sts = computeSafeToSpend(accounts, patterns, {asOf})`. Wrap in try/catch — on throw, skip the whole block (REQ-010).
  2. `debts = await store.loadDebts()`; build `accountById` from the already-loaded `accounts`.
  3. `ccMinimums` = Σ `minimum_payment` for debts whose account.kind === "credit" (0 if `!includeCcMinimums`).
  4. `autoLoan` = Σ `minimum_payment` for debts whose account.kind === "loan" (0 if `!includeAutoLoan`).
  5. `rent` via `resolveRent()` (below).
  6. `total = round2(rent + ccMinimums + autoLoan)`; `corrected = round2(raw - total)`; `deltaPct` per REQ-007.

### `resolveRent(cfg, store, asOf)` (same file, helper)
- If `cfg.overrideMonthly != null` → `{value: overrideMonthly, source:"override"}`.
- Else if `detectFromTransactions`: load txns over `[asOf − 4 months, asOf]` via `store.loadTransactionsInRange`; filter `merchant_normalized.toLowerCase().includes(merchantMatch.toLowerCase())`; group `-amount` by `YYYY-MM`; drop the current month (partial); if ≥1 prior month → average those monthly sums → `{value: round2(avg), source:"observed"}`.
- Else → `{value: expectedMonthly ?? 0, source:"config"}`.

> Rent model note (OQ-1): exactly one rent/CC/loan obligation falls in any 30-day window, so subtracting one month of each models the next-due reserve. We do not currently subtract `expected_outflows` already counted by the forecaster — accepted for v0.1.

### CLI wrapper (family-finance/src/k2-snapshot.ts)
- Read `data/fixed-costs.json` (reuse existing `readFileSync` + JSON.parse pattern already in the file's `loadEnv`); pass parsed config as `fixedCosts` to `buildK2Snapshot`. Missing/invalid file → pass `undefined` (block skipped, never crashes the emitter).

### `renderFamilyFinanceCard()` (k2-dashboard/index.html)
- After computing `stale`, read `const sts = s.safeToSpend`.
- If `sts` present, build a `badgeBlock` inserted directly under the card header (above the Net MTD row) so the corrected number is the card's headline.
- Layout (single block):
  - Big corrected figure `$X,XXX` (color: red when `!stale && sts.deltaPct > sts.redThresholdPct`, else normal/green-ish accent).
  - To its right, de-emphasized `raw $Y,YYY` with line-through and a delta chip `−$total (deltaPct%)`.
  - Below: small breakdown line `Reserved: rent $r · cards $c · auto $a`.
  - When `stale`: apply `numDim`, skip red logic (REQ-009).
- Guard: existing early-return `if (!s.netPosition || !s.burnRate)` stays; badge is additive and independently guarded by `if (sts)`.

## Sequence — happy path
1. Cron fires emitter → emitter reads fixed-costs.json, computes block, prints JSON.
2. Cron jq-merges into data.json `familyFinanceSnapshot` (existing 4-safety-gate pattern, unchanged).
3. Dashboard loads → `renderFamilyFinanceCard()` → badge shows corrected headline + raw + delta + breakdown.

## Files touched
- **new** `family-finance/data/fixed-costs.json`
- **edit** `family-finance/src/skills/k2-snapshot.ts` (type + logic + resolveRent helper)
- **edit** `family-finance/src/k2-snapshot.ts` (load config, pass through)
- **edit** `k2-dashboard/index.html` (`renderFamilyFinanceCard` badge block)
- **new** spec files (this folder)
- Rebuild: `family-finance` `npm run build` so `dist/` reflects src (cron runs `dist/k2-snapshot.js`).

## Risks / mitigations
- **Double-count (OQ-1):** accepted for v0.1; transparent breakdown lets Ryan eyeball it.
- **Stale dist:** the cron runs compiled `dist/`; forgetting `npm run build` ships nothing. TASK includes explicit build + emitter run verification.
- **Old snapshot in data.json until next cron:** UI guard (REQ-009) renders the card unchanged until the field appears; we trigger the cron at ship time to populate immediately.
