# Tasks — K2 Archive System

**Version:** v0.2 (Phase 0 closed)

---

## Phase 0 — Verify the Spec (complete)

- [x] **TASK-001** — Confirm or reject every [INFERRED] requirement → v0.2 closed
- [x] **TASK-002** — Resolve Q-1 through Q-8 → recorded in design.md § 6
- [x] **TASK-003** — Delete affordance inventory → recorded in design.md § 1
- [x] **TASK-004** — Confirm no existing `archived` field collision → verified

---

## Phase 1 — Module + Filters (sequential, orchestrator)

- [ ] **TASK-005 [REQ-015]** — Audit K2Archive scaffolding against final spec; add `K2Archive.restoreLast()`, `saveDataWithRetry()`, orphan-undo guard
- [ ] **TASK-006 [REQ-001, REQ-008]** — Extend KINDS to full list per design.md § 1 (add action-inbox-item, clip, doc, growthArea; coexist policy for action-inbox-item)
- [ ] **TASK-007 [REQ-008]** — Add `K2Archive.notArchived` filter to every native renderer + doc modal open guard
- [ ] **TASK-008 [REQ-011]** — Palette: add "Restore most recently archived" action; ensure palette search hides archived items

---

## Phase 2 — Route Delete Affordances (4 parallel sub-agents)

Sub-agents work in isolated worktrees. Each agent owns one cluster end-to-end:
- read the existing function in `index.html`
- replace with K2Archive call (route + shift-modifier for hard-delete)
- update tooltip to mention ⇧+click
- commit in worktree

### Cluster A — Notes & Tasks
- [ ] **TASK-009 [REQ-009]** — Route `deleteNote` (card)
- [ ] **TASK-009b [REQ-009]** — Route `deleteCurrentNote` (editor modal)
- [ ] **TASK-010 [REQ-009]** — Route `deleteTask` (modal)
- [ ] **TASK-010b [REQ-009]** — Route `triageTask(id, 'delete')` (triage panel)

### Cluster B — Projects, Decisions, Clips
- [ ] **TASK-011 [REQ-009]** — Route `deleteProject`
- [ ] **TASK-013 [REQ-009]** — Route Decisions delete (locate handler)
- [ ] **TASK-017 [REQ-009]** — Route `deleteClip` — replace 2-tap confirm flow with K2Archive call

### Cluster C — Inbox surfaces
- [ ] **TASK-012 [REQ-009]** — Route `deleteInboxItem` (manual)
- [ ] **TASK-012b [REQ-009]** — Route `inboxAcceptSuggestion` w/ `suggestedBucket:'trash'` (AI auto-triage)
- [ ] **TASK-014 [REQ-009]** — Route WaitingFor delete (locate handler)
- [ ] **TASK-015 [REQ-009]** — Route SomedayMaybe delete (locate handler)
- [ ] **TASK-016 [REQ-009]** — Add archive affordance for ActionInbox (coexist with existing `hidden:true` dismiss)

### Cluster D — Docs, Growth, Stale-jot toast unify
- [ ] **TASK-018 [REQ-009]** — Route Docs delete + add archived-doc modal open guard
- [ ] **TASK-NEW-019 [REQ-009]** — Route `deleteGrowthArea` (new task; replaces dropped accomplishments task)
- [ ] **TASK-NEW-020 [REQ-014]** — Replace `_staleJotsShowUndoToast` calls with K2Archive's toast (retire `#stale-jots-undo-toast` DOM)

---

## Phase 3 — UX Polish (orchestrator)

- [ ] **TASK-021 [REQ-010]** — Verify shift+click hard-delete works on every routed affordance
- [ ] **TASK-022 [REQ-013]** — Mobile spot-check: tap trash, tap Undo, both work
- [ ] **TASK-023 [REQ-014]** — Confirm no toast collision after unifying stale-jot
- [ ] **TASK-024 [REQ-007]** — Confirm sidebar Trash badge updates live (already implemented; verify only)

---

## Phase 4 — Ship (orchestrator)

- [ ] **TASK-025** — Manual round-trip per kind (archive → in trash → restore → archive again → purge)
- [ ] **TASK-026** — Bump `sw.js` cache → `k2-hq-v31-archive-system`
- [ ] **TASK-027** — Final commit + push; update memory entry to status=archived

---

## Progress Log

(One line per task completion: `TASK-NNN ✓ <date> <commit-sha>`)
