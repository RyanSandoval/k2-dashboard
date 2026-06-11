🏛️ plan-visibility

# Requirements — K2 Plan Visibility Subsystem

**Version:** v0.1 (drafted 2026-06-11)
**Scope:** Three Mission-page panels that surface workspace `.md` plan files, spec-file open questions, and per-cron spend tier breakdown — the things K2 currently can't see without leaving the dashboard.

---

## Functional Requirements

### REQ-001 — Spec Open-Questions Inbox panel
The Mission page **shall** render an "Open Questions" panel listing every unresolved `[INFERRED]` marker and Open-Questions section item parsed from any `k2-dashboard/spec/*/requirements.md` (or `design.md`).

**Acceptance:** When `requirements.md` contains the literal token `[INFERRED]` or a heading matching `Open Questions` / `Decisions` followed by bullet rows, each unresolved row appears as a row in the K2 panel.

### REQ-002 — Confirm / override actions per question
Each Open Question row **shall** expose two actions: **Confirm** (mark resolved, stamp the spec file by replacing `[INFERRED]` with `[CONFIRMED <date>]` or appending `[CONFIRMED]` to the line) and **Override** (open an inline input → user types replacement text → cron rewrites the line on next pass).

**Acceptance:** Clicking Confirm modifies the source `.md` file via the K2 Spec Open Questions Sync cron's write phase. The row disappears from the K2 panel on the next refresh.

### REQ-003 — Spec file paths visible per row
Every Open Question row **shall** show the source file path (relative to workspace) + the line number (when detectable) so Ryan can open the file directly.

**Acceptance:** Hovering or tapping the row opens the file path in a tooltip; if a `vscode://` or `file://` link works on his MBA, the row is also clickable.

### REQ-004 — Workspace plan "Decision Needed" panel
The Mission page **shall** render a "Decisions Needed" panel listing every workspace-root `*PLAN*.md` / `*PLAN*.markdown` file that contains pending-decision markers: case-insensitive matches on `Awaiting`, `paused`, or any heading line containing `Decision` / `Decisions Needed` / `Pending`.

**Acceptance:** A plan file with `## Decision Needed: X` or a body line `**Status:** Awaiting sign-off` surfaces as a row with the matched snippet.

### REQ-005 — Days-since-modified staleness sort
The "Decisions Needed" rows **shall** sort by `daysSinceModified` (mtime of the .md file) descending — stalest first — and show that age inline (e.g. `12d`).

**Acceptance:** Stalest pending decision is row 1; a plan file modified today shows `0d`.

### REQ-006 — One-tap open from panel
Each Decisions Needed row **shall** expose a "Open file" action that emits a `file://` URL link (clickable) so Ryan can jump to the source.

**Acceptance:** Clicking the link opens the .md in the OS default handler.

### REQ-007 — Model spend tier widget
The existing Mission cron pulse widget **shall** show a 7-day rolling token-cost rollup per cron, with a small inline bar segmented by model tier (Opus / Sonnet / Haiku).

**Acceptance:** Each cron row gains a `$X.XX 7d` figure; below the cron list, a "Tier rollup" line shows total $ per tier for the last 7 days across ALL crons.

### REQ-008 — Over-tier flag
Any cron whose 7-day Opus spend is ≥ $1.00 AND whose payload model resolves to an Opus tier (`anthropic/claude-opus-*` or `claude-cli/claude-opus-*`) **shall** render a `💸 Opus → consider Sonnet` chip on its row.

**Acceptance:** A cron costing $2 on Opus over 7 days displays the chip; a Haiku cron at any cost does not.

### REQ-009 — Token cost source-of-truth
Cost figures **shall** be derived from `mcp__openclaw__cron action=runs` `usage.input_tokens` + `usage.output_tokens` aggregated by cron over the past 7 days, multiplied by published per-token rates baked into the cron prompt.

**Acceptance:** If Opus rate is $15/M input + $75/M output and a cron logged 1.0M input + 0.5M output over 7d, the cron row shows `$52.50 7d`.

### REQ-010 — No silent data loss
All cron writers in this subsystem **shall** follow the safe-merge pattern documented in [k2-data merge feedback memory] — read-modify-write via `jq` with the 4 safety gates (snapshot count, existing non-target key count, key set equality, size sanity).

**Acceptance:** Force-running each new cron preserves every other top-level key in data.json; aborts with non-zero exit on any gate violation.

### REQ-011 — Mission page placement
All three panels (Open Questions, Decisions Needed, Spend Tier) **shall** render on the Mission page in this order: Decisions Needed → Open Questions → existing Cron Pulse (now annotated with spend) → Tier rollup line.

**Acceptance:** Loading Mission shows the three new surfaces above-the-fold, no horizontal scroll, mobile-safe.

### REQ-012 — Idempotent crons + cooldown
All three writer crons **shall** be idempotent (re-running on the same source state produces no diff) and **shall** schedule at non-:00/:30 minute marks per cron-discipline guidance.

**Acceptance:** Manual force-runs back-to-back produce a 0-byte data.json delta (excluding `*MetaSnapshot` timestamp keys).

---

## Non-Functional Requirements

- **NFR-1** Every cron is `payload.lightContext: true` and `sessionTarget: 'isolated'` (lightContext rule).
- **NFR-2** Every cron default model is `claude-cli/claude-haiku-4-5` (cost rule).
- **NFR-3** No UI tables (Discord rule does not apply to dashboard HTML but Mission stays bullet/row style for consistency).
- **NFR-4** UI panels degrade silently if their backing data array is missing or empty.

---

## Out of Scope (v0.1)

- Sub-folder spec files beyond `k2-dashboard/spec/*/` (e.g. external repos with their own spec/).
- Auto-rewriting Open Question rows beyond Confirm + Override (e.g. AI suggestion).
- Cost rollups longer than 7 days.
- Real-time cron cost (snapshot is sufficient).
- Mobile drawer redesign — fits existing Mission layout.
