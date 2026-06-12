🏛️ family-finance-card

# Design — K2 Family Finance Snapshot Card

**Version:** v0.1

---

## Data Flow

```
family-finance Node service
  ├── data/<YYYY-MM>/transactions.jsonl      (REQ-001 family-finance store)
  ├── data/state.json (accounts)
  ├── data/budgets.json
  ↓
src/skills/k2-snapshot.ts (NEW)              (REQ-026 family-finance)
  ↓ stdout (compact JSON, ≤2KB)
  ↓
OpenClaw cron "K2 Family Finance Snapshot"   (THIS spec REQ-007)
  ↓ jq merge into RyanSandoval/k2-data/data.json
  ↓
DATA.familyFinanceSnapshot                   (THIS spec REQ-001)
  ↓
k2-dashboard/index.html renderFamilyFinanceCard()
```

---

## Snapshot Shape

```ts
type FamilyFinanceSnapshot = {
  computedAt: string;          // ISO
  monthLabel: string;          // "2026-06"
  netPosition: {
    mtdNet: number;            // sum of tx.amount for current month (signed; - = net spend)
    mtdIncome: number;         // sum of positive amounts
    mtdSpend: number;          // sum of |negative| amounts (always positive number)
    deltaPctOfIncome: number;  // (|mtdNet|/mtdIncome)*100 if income > 0
  };
  burnRate: {
    monthSpendSoFar: number;        // discretionary only — excludes Transfers/Investments/Income/Rewards
    monthBudgetTotal: number;       // sum of monthly Budget records, expanded weekly/quarterly/annual into monthly equivalent
    pctOfBudget: number;
    daysIntoMonth: number;
    daysInMonth: number;
    projectedEndOfMonth: number;    // linear extrapolation: spend * (daysInMonth / daysIntoMonth)
    status: 'ok' | 'watch' | 'over';   // green ≤100, yellow ≤110, red >110
  };
  topCategory: {
    name: string;
    amountSpent: number;
    pctOfDiscretionary: number;
    txCount: number;
  };
  freshness: {
    lastSimpleFinSyncAt: string;     // most recent account.last_synced_at
    staleMinutes: number;
    stale: boolean;                   // true if > 24h
  };
};
```

Stored in `data.json` under two keys:
- `familyFinanceSnapshot`: the object above
- `familyFinanceSnapshotMeta`: `{ writtenAt: ISO, source: 'k2-family-finance-snapshot-cron' }`

---

## Components

### `family-finance/src/skills/k2-snapshot.ts` (new)
Pure function `buildK2Snapshot()` that:
1. Reads accounts from store; computes `staleMinutes = (now - max(account.last_synced_at)) / 60000`.
2. Reads current month transactions via `loadTransactionsInRange(monthStart, now)`.
3. Computes `mtdIncome`, `mtdSpend`, `mtdNet`.
4. Reads budgets (`data/budgets.json`); normalizes all to monthly amounts; sums.
5. Filters discretionary spend (`category` not in `['Transfers','Investments','Income','Rewards']`); buckets by category; picks top; computes burn.
6. Returns the snapshot object.

`family-finance/src/k2-snapshot.ts` is the CLI thin wrapper:
```ts
import { buildK2Snapshot } from './skills/k2-snapshot';
buildK2Snapshot().then(s => console.log(JSON.stringify(s))).catch(e => { console.error(e); process.exit(1); });
```

`package.json` script: `"emit:k2-snapshot": "node dist/k2-snapshot.js"`.

### OpenClaw cron `K2 Family Finance Snapshot`
- Schedule: `17 9-21/0,2,4 * * *` America/Los_Angeles (every 2h during work hours, off the :00/:30 mark)
- Model: `claude-cli/claude-haiku-4-5`, isolated, `lightContext: true`, `timeoutSeconds: 180`
- Bash:
  1. `cd ~/.openclaw/workspace/family-finance && npm run emit:k2-snapshot 2>/tmp/k2_ff_err.log > /tmp/k2_ff_snapshot.json`
  2. Validate snapshot is JSON with required keys; if not, fail with `family_finance_snapshot error: emitter output invalid`.
  3. File-based curl GET `data.json`, jq merge with `familyFinanceSnapshot = <snapshot>` + `familyFinanceSnapshotMeta = {writtenAt:NOW, source:"..."}`.
  4. 4 safety gates (snapshot has required keys + size; existing data has ≥5 non-target keys; key set unchanged; size not halved).
  5. PUT.

### `k2-dashboard/index.html` extensions
- HTML: new card container `<div id="dashboard-family-finance-card">` inserted in the Dashboard page below the Today/Planner block.
- JS:
  - `renderFamilyFinanceCard()` — reads `DATA.familyFinanceSnapshot`, renders the 3 metrics + freshness chip.
  - `_copyFFDailyBriefPrompt()` — copies `@K2 fire family-finance daily check-in` to clipboard + toast.
  - Called from existing `renderDashboard()` (or `renderHome()`/equivalent — confirm during build).

---

## Rendering Rules

- **Net position delta** row: arrow icon, sign-aware color (red if mtdNet negative AND deltaPctOfIncome > 100, green if mtdNet positive, dim otherwise).
- **Burn rate** row: tri-color status (`ok` green, `watch` yellow, `over` red). Show projected EOM in muted text after the slash.
- **Top category** row: category name in accent color, `$amount (XX% of spend)`.
- **Freshness** row: small `Xm ago` text; STALE chip in yellow when `stale: true`.

When `freshness.stale: true`:
- Dim all numeric rows.
- Replace burn-rate status color with grey.
- Add inline italic note: `data stale — projections paused`.

---

## File Layout (THIS spec)

```
k2-dashboard/
  spec/
    family-finance-card/
      requirements.md     <- REQ-001..009 + NFRs
      design.md           <- this file
      tasks.md            <- ordered build steps
      .spec-driven        <- marker

family-finance/
  src/skills/k2-snapshot.ts   <- NEW (REQ-026)
  src/k2-snapshot.ts          <- NEW CLI wrapper
  package.json                <- + script "emit:k2-snapshot"
  tasks.md                    <- + TASK-034
  requirements.md             <- + REQ-026 (K2 dashboard snapshot emit)
```

---

## Inferred / To Verify

- **[INFERRED]** Dashboard page render function is `renderDashboard()` (or similar). Confirm by reading existing dashboard render fn during TASK-005 below; adjust insertion point if it's a different name.
- **[INFERRED]** Burn-rate status thresholds (100/110) align with family-finance budget watch/over flags in `computeBudgetVariance`. Verify during build.
- **[INFERRED]** "Net position delta" is interpreted as MTD net cash flow (income − spend), NOT change in total liquid balance vs last month. Family-finance doesn't snapshot historical balances; this is the most honest metric available without that history. Reconfirm with Ryan if he wanted historical-balance delta.
