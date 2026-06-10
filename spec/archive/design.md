# Design — K2 Archive System

**Version:** v0.2 (Phase 0 closed)
**Companion to:** `requirements.md`

---

## 1. Data Model

### Per-item fields
Added to every archivable item:

| Field | Type | Set by | Cleared by |
|---|---|---|---|
| `archived` | `boolean` | `K2Archive.archive()` | `K2Archive.restore()`, `K2Archive.purge()` |
| `archivedAt` | ISO string | `K2Archive.archive()` | `K2Archive.restore()`, `K2Archive.purge()` |
| `archivedHard` | `boolean` (optional) | `K2Archive.archive(..., {hard:true})` | timer expiry or `K2Archive.restore()` |

### KINDS table (verified)

| Kind name | DATA key | Renderer | Notes |
|---|---|---|---|
| `note` | `notes` | `renderNotes` | Two delete paths: `deleteNote` (card) + `deleteCurrentNote` (editor modal) |
| `task` | `tasks` | `renderTasks` | Two delete paths: `deleteTask` (modal) + `triageTask(id,'delete')` (triage panel) |
| `project` | `projects` | `renderProjects` | `deleteProject` 2-click confirm flow |
| `inbox` | `inbox` | `renderInbox` | Two paths: `deleteInboxItem` (manual) + `inboxAcceptSuggestion` w/ `suggestedBucket:'trash'` (AI auto-triage) |
| `waiting` | `waitingFor` | `renderWaitingFor` | |
| `someday` | `somedayMaybe` | `renderSomeday` | |
| `decision` | `decisions` | `renderDecisions` | |
| `action-inbox-item` | `actionInbox` | `renderActionInbox` | Coexists with existing `hidden:true` (AI rank dismiss) — archive is user-intent |
| `clip` | `bookmarks` | `renderClips` (calls inner `renderClipsList`) | `deleteClip` is 2-tap confirm; replace whole flow with K2Archive call |
| `doc` | `docs` | `renderDocs` | Also guard doc modal / direct-open paths |
| `growthArea` | `growthAreas` | rendered inside `renderAccomplishments` | `deleteGrowthArea` at index.html:12559 |

### Delete affordance inventory (verified by Sonnet 4.6, 2026-06-09)

| Surface | Function | Approx line |
|---|---|---|
| Notes (card) | `deleteNote` | ~9406 |
| Notes (editor modal) | `deleteCurrentNote` | ~9031 |
| Tasks (modal) | `deleteTask` | ~6548 |
| Tasks (triage) | `triageTask(id,'delete')` | ~6977, 7820 |
| Projects | `deleteProject` | ~6831 |
| Inbox (manual) | `deleteInboxItem` | ~13516 |
| Inbox (AI auto-triage) | `inboxAcceptSuggestion` → trash bucket | callers around 13500 |
| Decisions | tbd — agents verify in their cluster |
| WaitingFor | tbd | |
| Someday | tbd | |
| Action Inbox dismiss | tbd; coexists with `hidden:true` | |
| Clips | `deleteClip` | ~8252 |
| Docs | tbd | |
| GrowthAreas | `deleteGrowthArea` | ~12559 |

### data.json archive-field hygiene
No existing kind uses `archived`/`archivedAt` for other purposes (verified by Phase 0 inspection).

---

## 2. Components

### `K2Archive` global module (IIFE)
Public API:
```js
K2Archive.archive(kind, id, { hard = false })
K2Archive.restore(kind, id)
K2Archive.purge(kind, id)
K2Archive.purgeAll()
K2Archive.restoreLast()            // for palette "Restore most recently archived"
K2Archive.isArchived(item)
K2Archive.notArchived(item)
K2Archive.renderTrash()
K2Archive.renderTrashBadge()
```

Private state:
- `KINDS` — kind → { arr, label, render } metadata (full list per § 1 table above)
- `_pendingPurge` — `Map<"${kind}:${id}", timeoutId>` for hard-delete undo window
- `_activeToast` — single in-flight toast handle (one toast at a time; replaces previous)

### Toast UI (`.k2arch-toast`)
Single-toast policy across the dashboard. Replaces both the existing global `showToast` for archive events and the standalone `_staleJotsShowUndoToast`.

Anatomy: label + tabular countdown (8s → 1s) + Undo button. Slides up from bottom-center; auto-dismisses on expiry; visually distinct only in that Undo is accent-colored.

### Trash page (`page-trash`)
- Header: count + Empty trash button
- Rows: kind tag + label + `archivedAt` + Restore + Delete
- Empty state: "Trash is empty. Archived items appear here for safekeeping."

### Renderer filter pattern
Every native renderer prepends:
```js
items = items.filter(K2Archive.notArchived);
```
Same pattern in every surface, applied right after raw-array read.

---

## 3. Sequence Flows

### 3.1 Soft archive (default trash-icon click)
```
User clicks 🗑 → deleteX(id) → K2Archive.archive(kind, id)
  → item.archived = true; item.archivedAt = now
  → KINDS[kind].render() + renderTrash() + renderTrashBadge()
  → await saveDataWithRetry()      ← 409-retry logic
  → toast({ label: "X archived: <name>", undo: () => restore })
    └─ on Undo (within 8s): item.archived = false; saveData(); re-render
    └─ on expire: nothing further
```

### 3.2 Hard delete (shift+click trash)
```
User shift+clicks 🗑 → deleteX(id, { hard:true }) → K2Archive.archive(kind, id, {hard:true})
  → item.archived = true; archivedHard = true; archivedAt = now
  → KINDS[kind].render() + renderTrash() + renderTrashBadge()
  → await saveDataWithRetry()
  → setTimeout 8000ms (timerKey = `${kind}:${id}`):
      → if item still present in DATA[arr] (orphan guard) → splice
      → await saveDataWithRetry()
      → renderTrash() + renderTrashBadge()
  → toast({ label: "X deleted: <name>", undo: () => clearTimer + restore })
```

### 3.3 Restore (from Trash page or palette action)
```
User clicks Restore → K2Archive.restore(kind, id)
  → if _pendingPurge has key → clearTimeout, delete from map
  → unset item.archived/archivedAt/archivedHard
  → await saveDataWithRetry()
  → KINDS[kind].render() + renderTrash() + renderTrashBadge()
```

### 3.4 Empty trash
```
User clicks Empty trash → confirm()
  → for each KIND: DATA[arr] = DATA[arr].filter(notArchived)
  → await saveDataWithRetry()
  → renderTrash() + renderTrashBadge() + every KIND render()
  → toast({ label: "N items purged", undoFn: null, duration: 3000 })
```

### 3.5 Cmd+K → "Restore most recently archived"
```
Palette action runs K2Archive.restoreLast():
  → collect all archived items across KINDS, sort by archivedAt desc
  → if empty → toast "Nothing to restore"
  → else → K2Archive.restore(kind, id) on the top one
```

### 3.6 `saveDataWithRetry()` — 409 race recovery (REQ-017)
```
async function saveDataWithRetry(retries = 1):
  try { await saveData(); return; }
  catch (e):
    if (e.status === 409 && retries > 0):
      await loadData()
      // re-apply the archive flag if the item still exists in the freshly-loaded DATA
      reapplyPendingArchiveFlags()
      return saveDataWithRetry(retries - 1)
    throw e
```
The existing `saveData()` already calls `loadData()` on 409 but returns without re-saving — that's the silent-loss bug. The retry wrapper re-applies the flag after the fresh load.

### 3.7 Orphan-undo guard (REQ-018)
The toast's Undo handler checks whether the item still exists in `DATA[arr]` (find by id) before calling restore. If missing (purged manually within the undo window), Undo dismisses the toast and no-ops.

```js
undoFn: async () => {
  const stillThere = DATA[meta.arr].find(x => String(x.id) === String(id));
  if (!stillThere) { /* orphan */ return; }
  // ... normal restore ...
}
```

---

## 4. UI Conventions

| Element | Style |
|---|---|
| Trash icon in row | Existing per-surface 🗑 button — no visual change |
| Toast | `.k2arch-toast`, 280px min, accent Undo text, tabular countdown |
| Trash page row | `.k2arch-row` — kind tag (uppercase, dim chip) + label + timestamp + buttons |
| Sidebar badge | Existing `.badge` class, accent-colored, shows count |
| Trash icon in sidebar | `🗑️ Trash` under Reference section |

---

## 5. Failure Modes (resolved)

| Mode | Behavior |
|---|---|
| Network save fails (5xx) | Existing `saveData()` error path. Archive flag stays in memory; on next load may be lost. v1 accepted risk; v2 could add a write-ahead queue. |
| `saveData()` 409 race | **Resolved by REQ-017**: `saveDataWithRetry()` re-applies flag after fresh load. |
| Two archives in quick succession | Single-toast policy: second toast replaces first; first toast's Undo forfeit. By design per REQ-014. |
| Hard-delete + manual purge race | **Resolved by REQ-018**: Undo button guards against orphan item; no-ops silently. |
| Renderer not yet defined | `render: () => window.renderX && renderX()` guard. |
| User closes tab mid-undo-window | Hard-pending item stays archived; timer dies. Item appears in Trash on next load with `archivedHard:true` but no timer running. Trash treats these as normal archived rows; manual Restore or Delete required. |

---

## 6. Open Questions (resolved 2026-06-09)

| ID | Question | Decision |
|---|---|---|
| Q-1 | Archive `dailyDocs` / jots? | **No** — out of scope v1 (date-keyed, ephemeral). |
| Q-2 | Action Inbox dismiss aliased to archive? | **No** — coexist. `hidden:true` stays the AI rank dismiss; archive is separate user-intent. |
| Q-3 | Cmd+K surfaces archived items? | **No** — hide archived from palette search. Only Trash page (and "Restore last archived" action) surface them. |
| Q-4 | Clips array name? | `DATA.bookmarks` (verified). |
| Q-5 | Accomplishments renderer? | `renderAccomplishments` (verified); no delete affordance today — kind is `growthArea` instead, deleted via `deleteGrowthArea`. |
| Q-6 | Docs deep-link/modal bypass? | **No bypass** — doc modal open path and direct render path both check `archived` and refuse to open archived docs (show "open Trash to restore" notice). |
| Q-7 | AI auto-triage to trash bypasses K2Archive? | **Route through K2Archive** — `inboxAcceptSuggestion` with `suggestedBucket:'trash'` calls `K2Archive.archive('inbox', id)` instead of `deleteInboxItem`. |
| Q-8 | `project.nextSteps[]` sub-items? | **Out of scope v1** — sub-items, not first-class. Per-project delete affordances unchanged. |
