🏛️ plan-visibility

# Design — K2 Plan Visibility Subsystem

**Version:** v0.1

---

## Data Model (k2-data `data.json` new keys)

### `DATA.specOpenQuestions: Array<Row>`
```ts
type SpecQuestionRow = {
  id: string;            // sha1(file:line:text).slice(0,10)
  file: string;          // absolute path
  fileShort: string;     // relative-to-workspace, e.g. spec/plan-visibility/requirements.md
  lineNo: number | null; // 1-based; null if scoped to a section header
  marker: '[INFERRED]' | 'OPEN_Q';
  text: string;          // first 240 chars of the raw line
  status: 'open' | 'confirmed' | 'overridden';
  confirmedAt?: string;  // ISO
  overrideText?: string;
  detectedAt: string;    // ISO of first time row was seen
};
```

Written by **K2 Spec Open Questions Sync** cron (every 30 min during work hours).
Read by `renderSpecOpenQuestionsPanel()` on Mission page.

### `DATA.decisionsNeeded: Array<Row>`
```ts
type DecisionRow = {
  id: string;             // sha1(file).slice(0,10)
  file: string;
  fileShort: string;
  basename: string;       // e.g. WEBMCP_VIKING_PLAN
  snippet: string;        // first matched line, ≤200 chars
  marker: 'Awaiting' | 'Paused' | 'Decision Needed' | 'Pending';
  mtimeMs: number;        // file mtime
  daysSinceModified: number;
  scannedAt: string;      // ISO
};
```

Written by **K2 Workspace Decision Scanner** cron (daily 7:23am PT).
Read by `renderDecisionsNeededPanel()`.

### `DATA.cronSpend: { rollup: TierRollup; byJob: Map<jobId, JobSpend>; computedAt: string }`
```ts
type TierRollup = {
  opus: number;     // dollars 7-day
  sonnet: number;
  haiku: number;
  unknown: number;
  total: number;
};
type JobSpend = {
  jobId: string;
  name: string;
  tier: 'opus' | 'sonnet' | 'haiku' | 'unknown';
  inputTokens: number;
  outputTokens: number;
  dollars: number;      // 7-day
  runCount: number;
  overTier: boolean;    // true when tier='opus' AND dollars >= 1.00
};
```

Written by **K2 Cron Spend Rollup** cron (every 2 hours during work).
Annotates rows in existing pulse widget; rollup line below.

---

## Rate Card (frozen v1)

Hardcoded in the spend rollup cron prompt. Update by editing the cron only.

| Tier   | Input $/M tokens | Output $/M tokens |
|--------|------------------|-------------------|
| Opus   | 15.00            | 75.00             |
| Sonnet | 3.00             | 15.00             |
| Haiku  | 0.80             | 4.00              |
| (other)| 0                | 0                 |

Tier resolution from `payload.model`:
- contains `opus` → opus
- contains `sonnet` → sonnet
- contains `haiku` → haiku
- else → unknown

---

## Components (UI)

### `renderMissionPage()` — extended
Order on Mission page:
1. Mission editor (existing)
2. `mission-decisions-needed-list` (REQ-004/005/006)
3. `mission-spec-questions-list` (REQ-001/002/003)
4. `mission-cron-list` (existing; now annotated with `$X.XX 7d` chips + `💸 Opus → consider Sonnet` chips)
5. `mission-spend-rollup` strip (REQ-007 tier rollup)

Add corresponding `<div id>` containers to the existing Mission HTML.

### Inline edit / confirm for spec questions
`confirmSpecQuestion(id)` and `overrideSpecQuestion(id)` mutate `DATA.specOpenQuestions[i].status` + `.confirmedAt|.overrideText` and call `saveData()`. Next cron pass picks up the change and writes through to the source `.md` file.

### Helpers reused
`_relTime(ms)`, `_cronIsRunning(j)`, `showToast()` — already present.

---

## Crons

Three new isolated agentTurn crons, all model=`claude-cli/claude-haiku-4-5`, `lightContext: true`, with jq+safety-gate writer pattern.

### `K2 Spec Open Questions Sync` — every 30 min during work hours
- Discovers files under `k2-dashboard/spec/*/(requirements|design).md`
- Parses `[INFERRED]` tokens and any heading `^## (Open Questions|Decisions)` followed by `^[-*] ` rows until next heading
- Loads existing `DATA.specOpenQuestions` to preserve `status/confirmedAt/overrideText` per `id`
- For rows where `status: 'confirmed'`, rewrites the source `.md` by replacing `[INFERRED]` with `[CONFIRMED <YYYY-MM-DD>]` on the matching line. For `status: 'overridden'`, rewrites the line text.
- Merges new array into data.json with jq + gates

### `K2 Workspace Decision Scanner` — daily 7:23am PT
- Discovers `*PLAN*.md` + a curated list of always-scan files (`K2-DASHBOARD.md`, etc.)
- Greps for `(?i)^(##+.*\b(Decision|Decisions Needed|Pending|Awaiting|Paused)\b)|(\bAwaiting\b|\bPaused\b)`
- For each match → row with mtime + daysSinceModified
- Sorts and writes `DATA.decisionsNeeded`

### `K2 Cron Spend Rollup` — every 2 hours during work hours (`5 9-21/2 * * *`)
- Lists all enabled crons via `mcp__openclaw__cron action=list`
- For each, calls `action=runs` and sums `usage.input_tokens` + `usage.output_tokens` for runs in the last 7 days
- Resolves tier from `payload.model`
- Applies rate card → dollars
- Builds `byJob` map + `rollup`
- Writes `DATA.cronSpend` via jq merge

All three crons follow `[[feedback-k2-data-json-merge-pattern]]` exactly — abort on any gate failure.

---

## Sequence: Confirm Spec Question

```
User clicks Confirm on row #abc
  └─ UI sets DATA.specOpenQuestions[i].status='confirmed', confirmedAt=now
     └─ saveData() PUTs k2-data data.json
        └─ Row stays in array (still status:confirmed) until next sync cron pass
           └─ Sync cron sees status:confirmed, rewrites source spec file line:
              [INFERRED] foo  →  [CONFIRMED 2026-06-11] foo
           └─ On next sync pass, the [INFERRED] token is gone → row is no longer detected → cron drops it from the array
              (preserve previously confirmed rows in a `confirmedHistory` field if Ryan ever asks)
```

---

## File Layout

```
k2-dashboard/
  spec/
    plan-visibility/
      requirements.md   <- REQ-001 … REQ-012
      design.md         <- this file
      tasks.md          <- ordered build steps
      .spec-driven      <- marker
  index.html            <- new render funcs + panel containers
```

No new code files outside `index.html`. All cron prompts live inside the cron payload, not in repo.
