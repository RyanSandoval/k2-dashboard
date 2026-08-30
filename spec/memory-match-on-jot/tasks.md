🧠 memory-match-on-jot

# Tasks — K2 Memory Match on New Jot

**Version:** v0.1 (2026-06-21) — implemented in PR #12; corrected 2026-08-30, see requirements.md "Deviations"
**Implements:** requirements.md + design.md
**Repo:** `/Users/ryansandoval/k2-dashboard/index.html` (single-file)
**Branch convention:** `feature/memory-match-on-jot`

---

## Phase 0 — Open Question Sign-off (BLOCKING)

Before any code:

- [x] **OQ-1 resolved**: no for MVP — Ryan signed off 2026-08-30
- [x] **OQ-2 resolved**: no for MVP — Ryan signed off 2026-08-30

---

## Phase 1 — Core Logic (no UI)

### TASK-001 — Add `_memTokenize` + stoplist
Write `_memTokenize(text) → Set<string>` with the 50-word stoplist. Place near the stale-jots utility functions (~line 4660).

**Test:** In browser console: `_memTokenize("Redesigning the flow for planning")` → `Set{'redesigning','flow','planning'}`.

### TASK-002 — Add `_memMatchScore`
Write `_memMatchScore(setA, setB) → number` (Jaccard). Place immediately after `_memTokenize`.

**Test:** `_memMatchScore(new Set(['flow','redesign','planning']), new Set(['planning','flow','ui']))` → `0.5`.

### TASK-003 — Add `_runMemoryMatch`
Write the full match runner per design.md. References `DATA.notes`, `DATA.dailyDocs`, `window._todayEditorDate`. Guards on min length (25 chars), excludes today's doc, filters archived notes.

**Test:** With a loaded dashboard, call `_runMemoryMatch()` in console. Verify it logs the top match (or null) without errors.

---

## Phase 2 — UI

### TASK-004 — Add `#jot-match-nudge` div
Insert the `<div id="jot-match-nudge" ...>` element immediately after `<div id="daily-doc-today-editor" ...>` in the jots page HTML (around line 2206).

**Test:** Element exists in DOM after page load. `display:none` by default.

### TASK-005 — Add `renderJotMatchNudge`, dismiss + navigate helpers
Write `renderJotMatchNudge(match)`, `_memMatchDismiss()`, `_memMatchNavigate(kind, id)`, `_memMatchExpandDoc(date)` per design.md.

**Test:** In console: `renderJotMatchNudge({ kind:'note', id: DATA.notes[0]?.id, title:'Test', text:'something about flow', date:'2026-06-01' })` → nudge appears below today's editor with title, snippet, Compare, ×.

---

## Phase 3 — Wire Up

### TASK-006 — Add `debouncedMemoryMatch` + hook into `_createTodayEditor`
1. Add the debounce wrapper near `debouncedJotLinker`.
2. In `_createTodayEditor.onUpdate`, after the existing `debouncedJotLinker()` call, add the `debouncedMemoryMatch()` call (guarded by `!isCheckboxToggle`).

**Test:** Type a sentence in today's editor. Wait 1.5s. Nudge appears (if match) or stays hidden (no match). No console errors.

---

## Phase 4 — Integration Test

### TASK-007 — End-to-end validation
1. Open dashboard on desktop (1400px) and mobile (375px).
2. Type content related to an existing note title → confirm nudge appears after 1.5s.
3. Tap "Compare →" → confirm note opens in editor panel.
4. Tap "×" → confirm nudge hides and stays hidden while same match is top-ranked.
5. Add new unrelated content that changes the top match → confirm nudge re-shows with new match.
6. Open browser console, run `console.time('match'); _runMemoryMatch(); console.timeEnd('match')` → confirm < 100ms.
7. Set editor content to < 25 chars → confirm no nudge.

---

## Acceptance Checklist (before PR)

- [ ] All 12 REQs pass their acceptance criteria
- [ ] `_runMemoryMatch()` < 100ms with full data set
- [ ] No console errors during normal jot editing
- [ ] Nudge visible on mobile at 375px (no overflow, no layout break)
- [ ] Archived notes never surface in nudge
- [ ] Today's doc never self-matches
- [ ] PR touches only `index.html`; no other files modified

---

## Estimated Effort

| Phase | Work |
|-------|------|
| Phase 0 | 0 code — decision only |
| Phase 1 (TASK-001–003) | ~50 lines, ~30 min |
| Phase 2 (TASK-004–005) | ~40 lines + 1 HTML element, ~30 min |
| Phase 3 (TASK-006) | ~8 lines, ~10 min |
| Phase 4 (TASK-007) | ~20 min validation |
| **Total** | **~90 min** |
