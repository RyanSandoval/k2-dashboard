🏛️ safe-to-spend-badge

# Requirements — SafeToSpend Reality-Corrected Finance Badge

**Version:** v0.1 (drafted 2026-06-20)
**Scope:** A badge on the existing K2 Dashboard "💰 Family Finance" card that shows SimpleFIN's raw safe-to-spend figure beside a *reality-corrected* figure — raw minus the fixed monthly obligations the forecaster misses (rent, credit-card minimums, the auto-loan). A delta chip shows how much was removed; the badge turns red when the correction exceeds a threshold.

**Source-of-truth coordination:** The safe-to-spend math + fixed-cost derivation live in `family-finance/` (emitter `src/skills/k2-snapshot.ts`, config `data/fixed-costs.json`). This spec covers that emitter extension AND the K2 render surface. Builds on [[family-finance-card]] (REQ-007 snapshot cron) which already delivers `DATA.familyFinanceSnapshot`.

**Why this exists:** Ryan manually subtracts rent + ~$885 CC minimums every time he reads safe-to-spend, because rent posts as a miscategorized "Subscriptions" charge (merchant `Bilt Eqr Web Pay`) that the recurring-pattern detector never catches, and CC/loan minimums aren't projected as outflows. The raw figure is therefore overstated by ~$5K every time. This bakes the correction into the surface he already looks at.

---

## Functional Requirements

### REQ-001 — Emitter outputs a safeToSpend block
`buildK2Snapshot` **shall** add a `safeToSpend` object to its output containing: `raw`, `corrected`, `deltaPct`, `fixedCostsOmitted {rent, ccMinimums, autoLoan, total}`, `rentSource`, and `redThresholdPct`.

**Acceptance:** Running `npm run emit:k2-snapshot` prints JSON whose `safeToSpend.corrected === round2(raw − fixedCostsOmitted.total)` and whose `fixedCostsOmitted.total === rent + ccMinimums + autoLoan`.

### REQ-002 — Raw figure comes from the existing forecaster
`raw` **shall** be `computeSafeToSpend(accounts, patterns, {asOf}).safe_to_spend` — the same function the morning brief uses. No reimplementation, no fabrication.

**Acceptance:** For a fixed `asOf`, the emitter's `safeToSpend.raw` equals the value `npm run analyze` prints for "SAFE TO SPEND TODAY" (within rounding).

### REQ-003 — CC minimums are derived, never hardcoded
`ccMinimums` **shall** be the sum of `minimum_payment` across all `debts.json` entries whose joined account (`debts[].account_id` → accounts) has `kind === "credit"`. Controlled by config flag `includeCcMinimums`.

**Acceptance:** With the current data set, `ccMinimums === 885`. Adding/removing a credit card in debts.json changes the figure on the next run with no code edit.

### REQ-004 — Auto-loan is derived from the loan account
`autoLoan` **shall** be the sum of `minimum_payment` across debts whose joined account has `kind === "loan"`. Controlled by config flag `includeAutoLoan`.

**Acceptance:** With the current data set, `autoLoan === 1042` (SchoolsFirst Tesla). Setting `includeAutoLoan:false` makes it `0`.

### REQ-005 — Rent is detected from transactions, with config fallback
`rent` **shall** be resolved in this precedence: (1) `config.rent.overrideMonthly` if non-null; else (2) observed trailing average of transactions whose `merchant_normalized` matches `config.rent.merchantMatch` (case-insensitive), averaged over complete prior calendar months in a 4-month lookback, when `detectFromTransactions` is true and at least one prior month matched; else (3) `config.rent.expectedMonthly`. `rentSource` **shall** record which path produced the value (`"override" | "observed" | "config"`).

**Acceptance:** With current data (Mar $3,000, Apr $3,348.36, May $3,175 of `Bilt Eqr Web Pay`), observed rent ≈ `$3,174.45` and `rentSource === "observed"`. Deleting all matched txns falls back to `expectedMonthly` with `rentSource === "config"`.

### REQ-006 — Config file is editable without code change
A new `family-finance/data/fixed-costs.json` **shall** hold rent config + the two include flags + `redThresholdPct`. Changing rent or a flag and re-running the emitter **shall** change the output with no rebuild.

**Acceptance:** Editing `expectedMonthly` then running `npm run emit:k2-snapshot` reflects the new value (verified via override path to avoid the observed-detection override).

### REQ-007 — deltaPct + red threshold
`deltaPct` **shall** be `round2(total / raw * 100)` when `raw > 0`, else `0`. The UI **shall** style the badge red when `deltaPct > redThresholdPct` (default 20).

**Acceptance:** raw $5,200, total $5,101 → deltaPct ≈ 98.1 → badge red. raw $30,000, total $5,101 → deltaPct ≈ 17.0 → badge not red.

### REQ-008 — Badge renders on the Finance card
The Finance card **shall** render the badge showing the corrected figure prominently, the raw figure de-emphasized beside it, the delta chip (`−$X (Y%)`), and a one-line breakdown of the three subtracted components.

**Acceptance:** Loading the dashboard with a snapshot containing `safeToSpend` shows all four elements; the corrected number is the visually dominant figure.

### REQ-009 — Graceful absence + stale handling
When `DATA.familyFinanceSnapshot.safeToSpend` is missing (old snapshot), the rest of the Finance card **shall** render unchanged with no empty badge container. When the snapshot is stale (existing `freshness.stale`), the badge **shall** dim consistently with the card's other rows and **shall not** apply red color-logic.

**Acceptance:** A snapshot without `safeToSpend` shows the card exactly as before this feature. A stale snapshot dims the badge and suppresses the red state.

### REQ-010 — No fabrication
If `raw` cannot be computed (no liquid accounts / forecaster throws) the emitter **shall** omit the `safeToSpend` key rather than emit a guessed value; the UI then falls back to REQ-009.

**Acceptance:** Forcing the forecaster to fail leaves the snapshot valid (other keys intact) and omits `safeToSpend`; card renders without the badge.

---

## Non-Goals (v0.1)
- Reconciling against obligations the forecaster *already* projects (potential double-count if a card payment is detected as recurring). Tracked as OQ-1; current behavior subtracts the full monthly fixed costs, matching Ryan's existing manual habit. Conservative (reserves more), strictly better than today's raw figure.
- Per-account drill-down UI / editing fixed costs from the dashboard (config is file-edited).
- Changing the morning-brief / intraday safe-to-spend wording (this is a dashboard surface only).

## Open Questions
- **OQ-1:** Should the correction skip a fixed cost already present in `safeToSpend.breakdown.expected_outflows` to avoid double-counting? Recommendation: defer; ship the conservative full-subtraction first, add reconciliation only if a real double-count is observed.
- **OQ-2:** Seed `expectedMonthly` at $3,174 (observed) — confirmed reasonable default; override path left null so detection drives the live number.
