# Tasks — K2 Archive System

**Phase 0 must complete before Phase 1+ unblock.** Each task: `TASK-NNN [REQ-NNN]: action` + Output + Verify.

---

## Phase 0 — Verify the Spec Matches Reality

### TASK-001 [requirements.md] — Confirm or reject every [INFERRED] requirement
Ryan reviews `requirements.md`. Corrections land as edits to that file, not as new tasks.
- _Output:_ `requirements.md` with [INFERRED] tags removed for confirmed reqs.
- _Verify:_ No remaining `[INFERRED]` tags in `requirements.md`.

### TASK-002 [design.md Q1–Q5] — Resolve open design questions
Answer Q-1 through Q-5 in `design.md` § 6. Updates land in `design.md` as decisions.
- _Output:_ `design.md` § 6 replaced with "Resolved" decisions.
- _Verify:_ No remaining `[TO VERIFY]` tags in `design.md` § 1 (data model) or § 2 (components).

### TASK-003 — Inventory all delete affordances in index.html
Grep for current delete entry points across surfaces. Inventory format: `<surface>: <function/handler> at L<line>`.
- _Output:_ Append the inventory to `design.md` § 1 as a new subsection "Delete affordance inventory (verified)".
- _Verify:_ Inventory matches `grep -nE "delete[A-Z]|onclick.*delete" index.html` output, plus any kebab-menu/modal Delete buttons.

### TASK-004 [REQ-012] — Verify no existing data.json items use the `archived` field
Pull live `data.json` and confirm no kind currently uses `archived`/`archivedAt` for other purposes.
- _Output:_ One-liner confirmation in `design.md` § 1.
- _Verify:_ `jq '[.notes,.tasks,.projects,.inbox,.waitingFor,.somedayMaybe,.decisions,.actionInbox,.bookmarks,.docs,.accomplishments] | flatten | map(.archived) | unique'` returns `[null]` or `[]`.

---

## Phase 1 — Finalize the K2Archive Module

### TASK-005 [REQ-015] — Audit current K2Archive scaffolding against final spec
Read the in-progress IIFE in `index.html`. Diff against `design.md` § 2 public API. List gaps in a comment block.
- _Output:_ Inline `// SPEC-GAP:` comments at any divergence.
- _Verify:_ Reading § 2 of `design.md` and the module side-by-side, the API surface matches exactly.

### TASK-006 [REQ-001, REQ-008] — Extend KINDS metadata per Phase 0 outcome
Add kinds confirmed in TASK-002 (action-inbox-item, clip, doc, accomplishment, optionally jot).
- _Output:_ Updated `KINDS` literal in `index.html` K2Archive module.
- _Verify:_ Every kind in `design.md` § 1 has a KINDS entry with arr/label/render set.

### TASK-007 [REQ-008] — Add `K2Archive.notArchived` filter to every native renderer
For each kind in KINDS, locate its render function and insert `items = items.filter(K2Archive.notArchived);` at the top of the filter chain.
- _Output:_ N edits to index.html (N = kinds count).
- _Verify:_ `grep -c "K2Archive.notArchived" index.html` = N + (any other intentional uses); manually archive one of each kind and confirm it disappears from its native page.

### TASK-008 [REQ-011] — Add palette entries: Trash page + "Restore last archived"
Both already partially done (Trash page added). Add the action.
- _Output:_ One new ACTIONS entry in K2Palette: `{ id: 'act-restore-last', icon: '↩️', label: 'Restore most recently archived', run: ... }`.
- _Verify:_ Cmd+K → type `restore` → action appears → Enter → most recent archived item restored, toast confirms.

---

## Phase 2 — Route Every Delete Affordance

One task per surface from TASK-003 inventory. All apply REQ-009.

### TASK-009 [REQ-009] — Route `deleteNote` (DONE — verify)
- _Verify:_ Clicking 🗑 on a note now archives (not hard-deletes); toast appears with Undo.

### TASK-010 [REQ-009] — Route `deleteTask` through K2Archive
Current impl is 2-click inline-confirm. Replace with single click → archive.
- _Output:_ `deleteTask` modified to call `K2Archive.archive('task', id, { hard: <shift-modifier> })`.
- _Verify:_ Delete a task from task modal → archived, toast shown, Trash count +1.

### TASK-011 [REQ-009] — Route `deleteProject` through K2Archive
Existing `confirm()` flow replaced.
- _Verify:_ Same as TASK-010 but for projects.

### TASK-012 [REQ-009] — Route Inbox item delete
Identify handler from TASK-003 inventory.
- _Verify:_ Inbox row trash → archived, restorable.

### TASK-013 [REQ-009] — Route Decisions delete
- _Verify:_ Decision card trash → archived, restorable.

### TASK-014 [REQ-009] — Route waitingFor delete
- _Verify:_ Waiting-for row delete → archived.

### TASK-015 [REQ-009] — Route somedayMaybe delete
- _Verify:_ Same.

### TASK-016 [REQ-009] — Resolve Action Inbox dismiss vs archive (per Q-2)
If aliased: K2Archive treats `hidden:true` items as archived.
If separate: dismiss stays; archive added as new affordance.
- _Verify:_ Per Q-2 decision; confirm behavior matches.

### TASK-017 [REQ-009] — Route Clips delete
- _Verify:_ Clip card trash → archived; respects Q-4 array name.

### TASK-018 [REQ-009] — Route Docs delete
- _Verify:_ Doc trash → archived.

### TASK-019 [REQ-009] — Route Accomplishments delete (if exists)
Skip if accomplishments has no delete affordance today.
- _Verify:_ Per inventory.

### TASK-020 [REQ-009] — Jot handling per Q-1
If jot archive in scope: add. If not: document as out-of-scope in `design.md`.

---

## Phase 3 — UX Polish

### TASK-021 [REQ-010] — Implement shift+click hard-delete on every trash button
Pass `{ hard: e.shiftKey }` from every onclick handler. Update tooltips ("⇧+click to delete immediately").
- _Verify:_ Shift+click trash on a note → toast says "deleted" not "archived"; after 8s undo window, note is spliced from `DATA.notes`.

### TASK-022 [REQ-013] — Verify mobile parity
Tap trash on note card in mobile viewport. Confirm toast renders correctly. Confirm Undo is touchable.
- _Verify:_ Manual test in Chrome devtools mobile emulation.

### TASK-023 [REQ-014] — Confirm no toast collision
Trigger an archive immediately after a `showToast` save confirmation. Confirm neither blocks the other awkwardly.
- _Verify:_ Visual inspection.

### TASK-024 [REQ-007] — Confirm sidebar Trash badge updates live
Archive an item. Restore it. Empty trash.
- _Verify:_ Badge increments/decrements/clears without page refresh.

---

## Phase 4 — Ship

### TASK-025 — Manual archive/restore/purge round-trip per kind
For each kind in final KINDS list: archive one → confirm absent from native page → confirm present in Trash → restore → confirm back on native page → archive again → purge → confirm gone everywhere.
- _Verify:_ Checklist completed; no console errors.

### TASK-026 — Bump `sw.js` cache version + final commit + push
- _Output:_ sw.js `k2-hq-v31-archive-system`, one final commit.
- _Verify:_ Two refreshes → new behavior on fresh load.

### TASK-027 — Update MEMORY entry to "archived" status
Mark the spec project archived in `MEMORY.md` once Phase 4 verifies clean.
- _Verify:_ MEMORY.md shows `archive/ — activated 2026-06-09, archived <date>`.

---

## Progress Log

(K-2 appends one line per task completion: `TASK-NNN ✓ <date> <commit-sha>`)
