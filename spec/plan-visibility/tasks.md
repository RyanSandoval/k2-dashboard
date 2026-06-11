🏛️ plan-visibility

# Tasks — K2 Plan Visibility Subsystem

**Version:** v0.1
Order: foundation (crons that write data) before UI (which depends on data being there).

---

## Phase 1 — Crons (writers)

- [ ] **TASK-001 [REQ-010, REQ-012, NFR-1, NFR-2]** Create cron **K2 Workspace Decision Scanner**
  - Schedule: `23 7 * * *` America/Los_Angeles (daily 7:23am PT)
  - isolated, lightContext, haiku
  - Discover plan files (`*PLAN*.md`, `K2-DASHBOARD.md`), grep for Decision/Awaiting/Paused/Pending markers, build `decisionsNeeded` array sorted by `daysSinceModified` desc
  - Write to `data.json` via jq merge with 4 safety gates
  - **Output:** cron job ID; one successful manual run
  - **Verify:** `gh api ... data.json` shows `decisionsNeeded` array with ≥3 rows and all other keys preserved (size delta < +5KB)

- [ ] **TASK-002 [REQ-001, REQ-002, REQ-010, NFR-1, NFR-2]** Create cron **K2 Spec Open Questions Sync**
  - Schedule: `13 9-15,19-21 * * *` America/Los_Angeles (every 30 min during work)
  - isolated, lightContext, haiku
  - Scan `k2-dashboard/spec/*/(requirements|design).md` for `[INFERRED]` + Open-Questions sections
  - Preserve `status/confirmedAt/overrideText` from existing array
  - For rows with `status:confirmed`, rewrite the source `.md` line to replace `[INFERRED]` → `[CONFIRMED <date>]`
  - For rows with `status:overridden`, rewrite the source line with `overrideText`
  - Merge `specOpenQuestions` into data.json via jq + gates
  - **Output:** cron job ID; one successful manual run
  - **Verify:** Plant a fake `[INFERRED]` in a test spec line, force-run, see row appear in `DATA.specOpenQuestions`; manually set `status: 'confirmed'`, force-run, see `[INFERRED]` replaced with `[CONFIRMED YYYY-MM-DD]`

- [ ] **TASK-003 [REQ-007, REQ-008, REQ-009, REQ-010, NFR-1, NFR-2]** Create cron **K2 Cron Spend Rollup**
  - Schedule: `7 9-21/2 * * *` America/Los_Angeles (every 2 hours during work)
  - isolated, lightContext, haiku
  - For each enabled cron: pull `runs` for the last 7 days, sum input+output tokens, resolve tier from `payload.model`, multiply by rate card, flag `overTier`
  - Build `{rollup, byJob, computedAt}` shape, write `DATA.cronSpend` via jq + gates
  - **Output:** cron job ID; one successful manual run
  - **Verify:** `data.json` contains `cronSpend` with `rollup.opus + rollup.sonnet + rollup.haiku = rollup.total ± 0.01` and at least one `byJob` entry; all other keys preserved

## Phase 2 — UI (panels)

- [ ] **TASK-004 [REQ-004, REQ-005, REQ-006, REQ-011, NFR-3, NFR-4]** Add **Decisions Needed** panel
  - New `mission-decisions-needed-list` container in Mission HTML, above the cron list
  - New `renderDecisionsNeededPanel()` function — reads `DATA.decisionsNeeded`, renders rows: title, mini-snippet, days chip, "Open file" link
  - Call from `renderMissionPage()`
  - **Verify:** Reload dashboard → panel renders with rows from the cron; empty state shows hint text

- [ ] **TASK-005 [REQ-001, REQ-002, REQ-003, REQ-011, NFR-3, NFR-4]** Add **Open Questions Inbox** panel
  - New `mission-spec-questions-list` container in Mission HTML
  - New `renderSpecOpenQuestionsPanel()` function — reads `DATA.specOpenQuestions`, filters `status === 'open'`, renders rows: spec file (relative path), line text, Confirm + Override buttons
  - New `confirmSpecQuestion(id)` + `overrideSpecQuestion(id)` mutators (set status, call saveData)
  - Call from `renderMissionPage()`
  - **Verify:** Plant a fake `[INFERRED]` in a spec file, wait for cron, see row in UI; click Confirm → row disappears within 30 min as cron rewrites the file

- [ ] **TASK-006 [REQ-007, REQ-008, REQ-011, NFR-3, NFR-4]** Annotate cron pulse + add **Tier rollup** strip
  - Modify `renderMissionCronList()`: per row, look up `DATA.cronSpend.byJob[jobId]` and append a `$X.XX 7d` chip (skip if 0); add `💸 Opus → consider Sonnet` chip when `overTier === true`
  - Append `mission-spend-rollup` strip below the cron list rendering: `Opus $X.XX · Sonnet $X.XX · Haiku $X.XX · Total $X.XX (last 7d, refreshed Nm ago)`
  - **Verify:** Reload Mission → rows show $ chips on annotated jobs; rollup line shows non-zero totals if any 7-day token usage exists

## Phase 3 — Wiring + Ship

- [ ] **TASK-007** Commit + push `index.html` + `spec/plan-visibility/` to `RyanSandoval/k2-dashboard`
  - **Verify:** `gh api repos/RyanSandoval/k2-dashboard/commits/main --jq '.commit.message | split("\n")[0]'` shows the new commit

- [ ] **TASK-008** Update workspace `MEMORY.md` Active Spec-Driven Projects with `k2-dashboard/spec/plan-visibility/` row
  - **Verify:** Line present in MEMORY.md
