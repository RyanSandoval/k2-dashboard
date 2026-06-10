# Requirements — K2 Archive System

**Version:** v0.2 (Phase 0 closed 2026-06-09 by Opus 4.7 + Sonnet 4.6 cross-check)
**Scope:** Unified archive/delete UX across every "item kind" surface in the k2-dashboard SPA.

---

## Functional Requirements

### REQ-001 — Universal soft-delete
Every archivable item kind (notes, tasks, projects, inbox, waitingFor, somedayMaybe, decisions, action-inbox-items, clips/bookmarks, docs, growthAreas) **shall** support being moved to a "Trash" state without being permanently removed from `data.json`.

Out of scope kinds: jots/dailyDocs (date-keyed, ephemeral), accomplishments (no delete affordance today), project.nextSteps (sub-items).

**Acceptance:** After an archive action, the item disappears from its native surface but remains retrievable from a Trash page.

### REQ-002 — Full restore
An archived item **shall** be restorable to its original surface with all original fields intact.

**Acceptance:** After restore, the item reappears on its native page and no fields are lost or mutated.

### REQ-003 — Inline Undo window
Every archive action **shall** surface an inline Undo affordance for **8 seconds** before the action is treated as final from the toast UI.

**Acceptance:** Toast shows "Undo" button + visible countdown; clicking it un-archives within the window.

### REQ-004 — Trash page
A `Trash` page **shall** list every archived item across all kinds, sorted by `archivedAt` (most recent first), with per-item **Restore** and **Permanently Delete** actions.

**Acceptance:** Navigating to `/trash` shows N rows where N = sum of archived items across all kinds.

### REQ-005 — Two-step purge
Permanent delete **shall** require explicit confirmation (browser `confirm()` or equivalent) before purging from `data.json`.

**Acceptance:** No item leaves `data.json` without two-step user intent.

### REQ-006 — Empty trash
The Trash page **shall** support a single **Empty trash** action that purges every archived item after confirmation.

**Acceptance:** Click "Empty trash" → confirm → all `archived:true` items removed from arrays in `data.json`.

### REQ-007 — Sidebar badge
A sidebar badge on the Trash nav item **shall** reflect the count of archived items, displaying `99+` when over 99 and hiding when zero.

### REQ-008 — Renderer filter
Every native surface renderer **shall** filter out items where `archived === true` so they never appear on their default page.

**Affected renderers:** `renderNotes`, `renderTasks`, `renderProjects`, `renderInbox`, `renderWaitingFor`, `renderSomeday`, `renderDecisions`, `renderActionInbox`, `renderClips`, `renderClipsList`, `renderDocs`, `renderGrowthAreas` (if exists; otherwise inside `renderAccomplishments`). Doc modal / doc deep-link open paths **shall** also check the archived flag and refuse to open archived docs.

**Acceptance:** An archived note does not appear on `/notes`; only on `/trash`. Direct-open of an archived doc surfaces "(archived — open Trash to restore)".

### REQ-009 — Every delete path routes through K2Archive
Every existing per-item delete affordance **shall** route through `K2Archive.archive()` instead of hard-deleting directly. This explicitly includes:
- Note card trash button (`deleteNote`)
- Note editor in-modal trash button (`deleteCurrentNote`)
- Task modal Delete (`deleteTask`)
- Task triage panel `triageTask(id, 'delete')`
- Project modal Delete (`deleteProject`)
- Inbox manual delete (`deleteInboxItem`)
- Inbox AI auto-triage trash bucket (`inboxAcceptSuggestion` with `suggestedBucket: 'trash'`)
- Decision delete
- WaitingFor delete
- SomedayMaybe delete
- Action Inbox dismiss is **distinct from** archive: keep `hidden:true` as the AI-ranking dismiss flag, add archive as a separate user-intent action
- Clip delete (`deleteClip` — current 2-tap confirm replaced)
- Doc delete
- GrowthArea delete (`deleteGrowthArea`)

**Acceptance:** `grep -nE "DATA\.(notes|tasks|projects|inbox|waitingFor|somedayMaybe|decisions|actionInbox|bookmarks|docs|growthAreas)\s*=.*\.filter\(" index.html` returns hits only inside `K2Archive` and in renderer filter chains for `notArchived`. No surface-specific `splice` or `filter`-out-by-id outside K2Archive.

### REQ-010 — Hard-delete shortcut
A hard-delete variant **shall** be available (shift+click on the trash button) for power users who want to skip the archive step. It still surfaces an Undo toast.

**Acceptance:** Shift+click trash → toast says "deleted" not "archived"; item marked `archivedHard:true` → spliced from array after 8s if undo not used.

### REQ-011 — Palette integration
The Cmd+K palette **shall** include a "Trash" page entry and a "Restore most recently archived" action.

The palette **shall not** surface archived items in search results.

**Acceptance:** Typing `trash` surfaces the page; typing `restore` surfaces the action; typing the title of an archived note returns no result.

### REQ-012 — Data model
The data model **shall** use these per-item fields rather than a separate `trash` array:
- `archived: boolean`
- `archivedAt: ISO string`
- `archivedHard: boolean` (optional; only set during the pending-purge window for hard deletes)

**Acceptance:** Item `id` remains stable through archive → restore → purge cycles; cross-references (e.g., a task's `linkedNoteId`) continue to resolve while archived.

### REQ-013 — Mobile parity
Mobile **shall** expose the same archive UX as desktop (trash button + Undo toast). Swipe-to-archive is **not** required for v1.

**Acceptance:** Tapping the trash icon on a note card in mobile triggers archive with toast; the Undo button is touchable.

---

## Non-Functional Requirements

### REQ-014 — Single-toast policy across all undo systems
The new archive toast (`.k2arch-toast`) **shall** be the single in-flight undo affordance. The existing standalone `_staleJotsShowUndoToast` (`#stale-jots-undo-toast`) **shall** be retired in favor of K2Archive's toast.

**Acceptance:** `grep -n "stale-jots-undo-toast" index.html` returns only the deletion in this work; only one `.k2arch-toast` exists in the DOM at any time.

### REQ-015 — Single source of truth
All archive logic **shall** live in one `K2Archive` module. Surface code may only invoke `K2Archive.archive/restore/purge/isArchived` — never touch `item.archived` directly.

**Acceptance:** `grep -nE "\.archived\s*=" index.html` returns matches only inside the K2Archive module.

### REQ-016 — Save discipline
Every archive/restore action **shall** call `saveData()` exactly once per phase:
- Soft archive: 1 save (after `archived=true`)
- Restore: 1 save
- Hard archive: 2 saves total (1 at archive, 1 when purge timer fires)
- Purge from Trash page: 1 save
- Empty trash: 1 save

**Acceptance:** Network panel shows exactly the expected save count per action; no interleaved saves.

### REQ-017 — 409 race recovery
If `saveData()` hits a 409 (sha conflict, another tab saved first), the archive **shall** retry once after a `loadData()` re-fetch, with the archive flag re-applied to the freshly-loaded item if it still exists.

**Acceptance:** Simulating 409 → archive flag persists after retry; no silent loss.

### REQ-018 — Orphan undo guard
If the user clicks Undo on a toast whose underlying item was already manually purged (from the Trash page) within the undo window, the Undo button **shall** no-op cleanly (toast dismisses, no data mutation, no save).

**Acceptance:** Hard-delete a note → open Trash → purge same note → Undo button → no error, no orphaned save.

---

## Out of Scope (v1)

- Auto-purge after N days
- Bulk multi-select archive
- Swipe-to-archive gestures on mobile
- Server-side trash retention policy (everything stays in `data.json` until purged)
- Archive of `dailyDocs` / jots (date-keyed structure; if a daily doc is empty user can delete the date key manually)
- Archive of `accomplishments` (no delete affordance exists today)
- Archive of `project.nextSteps` items (sub-items of a project, scoped per-project)
