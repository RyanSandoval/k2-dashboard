# Requirements — K2 Archive System

**Version:** v0-retrofit
**Activated:** 2026-06-09
**Scope:** Unified archive/delete UX across every "item kind" surface in the k2-dashboard SPA.

All requirements below are `[INFERRED]` from prior chat context with Ryan ("smooth and UX clear archive/delete across all surfaces"). Each must be confirmed or rejected before Phase 1 (implementation) tasks are unblocked.

---

## Functional Requirements

### REQ-001 [INFERRED] — Universal soft-delete
Every archivable item kind (notes, tasks, projects, jots, inbox, waitingFor, somedayMaybe, decisions, action-inbox-items, clips, docs, accomplishments) **shall** support being moved to a "Trash" state without being permanently removed from `data.json`.

**Acceptance:** After an archive action, the item disappears from its native surface but remains retrievable from a Trash page.

### REQ-002 [INFERRED] — Full restore
An archived item **shall** be restorable to its original surface with all original fields intact.

**Acceptance:** After restore, the item reappears on its native page and no fields are lost or mutated.

### REQ-003 [INFERRED] — Inline Undo window
Every archive action **shall** surface an inline Undo affordance for **8 seconds** before the action is treated as final from the toast UI.

**Acceptance:** Toast shows "Undo" button + visible countdown; clicking it un-archives within the window.

### REQ-004 [INFERRED] — Trash page
A `Trash` page **shall** list every archived item across all kinds, sorted by `archivedAt` (most recent first), with per-item **Restore** and **Permanently Delete** actions.

**Acceptance:** Navigating to `/trash` shows N rows where N = sum of archived items across all kinds.

### REQ-005 [INFERRED] — Two-step purge
Permanent delete **shall** require explicit confirmation (browser `confirm()` or equivalent) before purging from `data.json`.

**Acceptance:** No item leaves `data.json` without two-step user intent.

### REQ-006 [INFERRED] — Empty trash
The Trash page **shall** support a single **Empty trash** action that purges every archived item after confirmation.

**Acceptance:** Click "Empty trash" → confirm → all `archived:true` items removed from arrays in `data.json`.

### REQ-007 [INFERRED] — Sidebar badge
A sidebar badge on the Trash nav item **shall** reflect the count of archived items.

**Acceptance:** Badge shows accurate count, displays `99+` when over 99, hidden when zero.

### REQ-008 [INFERRED] — Renderer filter
Every native surface renderer **shall** filter out items where `archived === true` so they never appear on their default page.

**Affected renderers (incomplete list, [TO VERIFY]):** `renderNotes`, `renderTasks`, `renderProjects`, `renderInbox`, `renderWaitingFor`, `renderSomeday`, `renderDecisions`, `renderActionInbox`, `renderClips`, `renderDocs`, `renderAccomplishments`, `renderJots` (status [TO VERIFY] — jots are date-keyed).

**Acceptance:** An archived note does not appear on `/notes`; only on `/trash`.

### REQ-009 [INFERRED] — Single delete affordance
Every existing per-item delete affordance (trash icon, kebab menu, modal Delete button) **shall** route through `K2Archive.archive()` instead of hard-deleting directly.

**Acceptance:** No code path outside `K2Archive` mutates an item out of an array.

### REQ-010 [INFERRED] — Hard-delete shortcut
A hard-delete variant **shall** be available (shift+click or modifier) for power users who want to skip the archive step. It **still** surfaces an Undo toast.

**Acceptance:** Shift+click trash → item marked for hard purge after 8s undo window → spliced from array if undo not used.

### REQ-011 [INFERRED] — Palette integration
The Cmd+K palette **shall** include a "Trash" page entry and a "Restore most recently archived" action.

**Acceptance:** Typing `trash` surfaces the page; typing `restore` surfaces an action that restores the last archived item across all kinds.

### REQ-012 [INFERRED] — Data model
The data model **shall** use these per-item fields rather than a separate `trash` array:
- `archived: boolean`
- `archivedAt: ISO string`
- `archivedHard: boolean` (optional; only set during the pending-purge window for hard deletes)

**Acceptance:** Item `id` remains stable through archive → restore → purge cycles; cross-references (e.g., a task's `linkedNoteId`) continue to resolve while archived.

### REQ-013 [INFERRED] — Mobile parity
Mobile **shall** expose the same archive UX as desktop (trash button + Undo toast). Swipe-to-archive is **not** required for v1.

**Acceptance:** Tapping the trash icon on a note card in mobile triggers archive with toast; the Undo button is touchable.

---

## Non-Functional Requirements

### REQ-014 [INFERRED] — No regression on existing showToast
The new archive toast (`.k2arch-toast`) **shall** not break or be visually crowded by the existing global `showToast()` (used for save confirmations, AI ideas, etc.).

**Acceptance:** Triggering an archive while another `showToast` is visible → either stacks gracefully or replaces cleanly with no overlap.

### REQ-015 [INFERRED] — Single source of truth
All archive logic **shall** live in one `K2Archive` module. Surface code may only invoke `K2Archive.archive/restore/purge/isArchived` — never touch `item.archived` directly.

**Acceptance:** `grep -n "item\.archived\s*=" index.html` returns only matches inside the K2Archive module.

### REQ-016 [INFERRED] — Save discipline
Every archive/restore/purge operation **shall** call `saveData()` exactly once, after the data mutation and before the renderer re-runs, to avoid race conditions on the GitHub API.

**Acceptance:** No duplicate or interleaved `PUT data.json` requests in network panel during an archive action.

---

## Out of Scope (v1)

- Auto-purge after N days (Ryan didn't ask for this; can revisit)
- Bulk multi-select archive
- Swipe-to-archive gestures on mobile
- Server-side trash retention policy (everything stays in `data.json` until purged)
- Archive of `dailyDocs` (date-keyed structure; [TO VERIFY] in Phase 0)
