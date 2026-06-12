🏛️ family-finance-card

# Requirements — K2 Family Finance Snapshot Card

**Version:** v0.1 (drafted 2026-06-12)
**Scope:** A single Dashboard-page K2 card surfacing net position delta, budget burn rate, and biggest spend category for the current month. Reads from a snapshot written by a new cron that runs the family-finance project's emitter. Pre-wires the data flow that the broader family-finance app will eventually use for richer surfaces.

**Source-of-truth coordination:** Logic lives in `family-finance/` (see [[family-finance/requirements.md]] new REQ-026). This spec covers only the K2 surface + the cron that delivers the snapshot.

---

## Functional Requirements

### REQ-001 — Snapshot card on Dashboard page
The Dashboard page **shall** render a "💰 Family Finance" card immediately below the existing Today / Planner section.

**Acceptance:** Loading the dashboard shows the card when `DATA.familyFinanceSnapshot` exists; the card is absent (no empty container) when the snapshot key is missing.

### REQ-002 — Net position delta
The card **shall** show this month's net cash flow (sum of all transaction amounts for the current calendar month, in `America/Los_Angeles`) with a + or − prefix and a percent-of-income context line.

**Acceptance:** If MTD = −$1,234.56 on $5,000 income MTD, card shows `−$1,234.56 (24.7% of MTD income)`.

### REQ-003 — Budget burn rate
The card **shall** show month-to-date spend across all budgeted categories vs total monthly budget, with a percent figure and a "projected end-of-month" extrapolation.

**Acceptance:** If MTD spend = $800 on $1,925 monthly budget after 10 days of a 30-day month, card shows `Burn: $800 / $1,925 (42%) · Projected $2,400 EOM`. Color: green if projected ≤ budget, yellow ≤ 110%, red > 110%.

### REQ-004 — Biggest spend category
The card **shall** name the single category with the most MTD spend (excluding `Transfers`, `Investments`, `Income`, `Rewards`), with the dollar amount and a percent-of-total-spend figure.

**Acceptance:** If Dining is top at $432 of $1,200 discretionary MTD spend, card shows `Top: Dining $432 (36% of spend)`.

### REQ-005 — Freshness label
The card **shall** show how old the snapshot is (e.g. "3m ago"), and **shall** show a 🟡 STALE chip when the underlying SimpleFIN sync is >24h stale per REQ-N05 of [[family-finance/requirements.md]].

**Acceptance:** A snapshot computed 3 minutes ago shows "3m ago" with no chip; a SimpleFIN sync that's 36h stale shows the STALE chip and the burn/delta numbers are dimmed.

### REQ-006 — Open-in-Discord affordance
The card **shall** include a small "Run daily brief →" link/button that prompts Ryan to ask K-2 to fire the existing `npm run skill:daily-checkin` (no auto-trigger — Ryan opts in).

**Acceptance:** Clicking the link copies the canonical phrase (`@K2 fire family-finance daily check-in`) to clipboard with a toast confirming.

### REQ-007 — Snapshot writer cron
A new cron **K2 Family Finance Snapshot** **shall** invoke `node family-finance/dist/k2-snapshot.js` every 30 min during work hours, capture its JSON output, and write it to `data.json` under `familyFinanceSnapshot` via the jq-merge + 4-safety-gates pattern.

**Acceptance:** Force-running the cron writes a complete snapshot object; all other data.json keys remain intact (gates pass).

### REQ-008 — No fabrication
If the family-finance emitter exits with `stale: true` OR the SimpleFIN sync is >24h stale, the snapshot's numeric fields **shall** still be present but the UI **shall** show only the freshness chip + a "data stale" inline note in place of color-coded math.

**Acceptance:** Forcing a stale state produces a card showing the STALE chip and the words `data stale — projections paused` instead of green/yellow/red color logic. (Mirrors family-finance REQ-N05.)

### REQ-009 — Idempotent + non-destructive
The snapshot cron **shall** never mutate any other key in data.json. It writes exactly two keys: `familyFinanceSnapshot` and `familyFinanceSnapshotMeta`.

**Acceptance:** Force-running back-to-back produces a 0-byte delta of non-target keys.

---

## Non-Functional Requirements

- **NFR-1** Cron is `payload.lightContext: true`, `sessionTarget: 'isolated'`, model `claude-cli/claude-haiku-4-5`.
- **NFR-2** Cron uses file-based curl pattern (no bash `RESP=$(...)` for large JSON) per [[feedback-bash-variable-large-json]].
- **NFR-3** Card degrades silently when `DATA.familyFinanceSnapshot` is missing (no broken UI).
- **NFR-4** Card never displays raw account balances or account numbers — only the 3 aggregate metrics + freshness.
- **NFR-5** Snapshot emitter must run in under 5 seconds on a warm cache.

---

## Out of Scope (v0.1)

- Per-account balance breakdown on the card (privacy + scope creep).
- Weekly / quarterly / annual horizons on the card (daily brief covers it).
- Click-to-drill-down on a category (later, when more screen real estate is justified).
- Debt avalanche progress (already drilled in daily brief; would crowd the card).
- Goal progress (likewise).
