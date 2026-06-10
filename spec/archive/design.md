# Design — K2 Archive System

**Version:** v0-retrofit
**Companion to:** `requirements.md`

Every section marked `[TO VERIFY]` was inferred by K-2 from existing code reads. Confirm in Phase 0 before treating as canonical.

---

## 1. Data Model

### Per-item fields
Added to every archivable item (no migration needed — fields default to `undefined` which is treated as `archived: false`):

| Field | Type | Set by | Cleared by |
|---|---|---|---|
| `archived` | `boolean` | `K2Archive.archive()` | `K2Archive.restore()`, `K2Archive.purge()` |
| `archivedAt` | ISO string | `K2Archive.archive()` | `K2Archive.restore()`, `K2Archive.purge()` |
| `archivedHard` | `boolean` (optional) | `K2Archive.archive(..., {hard:true})` | timer expiry or `K2Archive.restore()` |

### Affected DATA arrays
[TO VERIFY] — current inventory based on KINDS metadata in the in-progress K2Archive module + outstanding surfaces:

| Kind name | DATA key | Renderer | Status |
|---|---|---|---|
| `note` | `notes` | `renderNotes` | scaffolded |
| `task` | `tasks` | `renderTasks` | scaffolded |
| `project` | `projects` | `renderProjects` | scaffolded |
| `inbox` | `inbox` | `renderInbox` | scaffolded |
| `waiting` | `waitingFor` | `renderWaitingFor` | scaffolded |
| `someday` | `somedayMaybe` | `renderSomeday` | scaffolded |
| `decision` | `decisions` | `renderDecisions` | scaffolded |
| `action-inbox-item` [TO VERIFY] | `actionInbox` | `renderActionInbox` | **not in KINDS yet** |
| `clip` [TO VERIFY] | `bookmarks` | `renderClips` | **not in KINDS yet** |
| `doc` [TO VERIFY] | `docs` | `renderDocs` | **not in KINDS yet** |
| `accomplishment` [TO VERIFY] | `accomplishments` | (renderer name [TO VERIFY]) | **not in KINDS yet** |
| `jot` [TO VERIFY — likely skip] | `jots` or `dailyDocs` | `renderJots` / `renderDailyDocs` | **structure differs** |

---

## 2. Components

### `K2Archive` global module
IIFE attached to `window.K2Archive`. Owns archive, restore, purge, render, badge.

Public API:
```js
K2Archive.archive(kind, id, { hard = false })  // soft delete + toast (or hard with timer)
K2Archive.restore(kind, id)                    // un-archive
K2Archive.purge(kind, id)                      // permanent remove
K2Archive.purgeAll()                           // empty trash
K2Archive.isArchived(item)                     // filter predicate
K2Archive.notArchived(item)                    // negated filter (renderer convenience)
K2Archive.renderTrash()                        // page renderer
K2Archive.renderTrashBadge()                   // sidebar badge updater
```

Private state:
- `KINDS` — kind → { arr, label, render } metadata
- `_pendingPurge` — Map<`${kind}:${id}`, timeoutId> for hard-delete undo window
- `_activeToast` — single in-flight toast handle (one toast at a time; replaces previous)

### Toast UI (`.k2arch-toast`)
Single-toast policy. Slides up from bottom-center, shows label + countdown (`8s`...`1s`) + Undo button. Auto-dismisses on expiry. Replaces any existing `.k2arch-toast` if a new archive fires.

### Trash page (`page-trash`)
Header: count + Empty trash button.
Rows: kind tag + label + `archivedAt` timestamp + Restore + Delete buttons.
Empty state: "Trash is empty. Archived items appear here for safekeeping."

### Renderer filter pattern
Every native renderer prepends:
```js
items = items.filter(K2Archive.notArchived);
```
Inserted at the same position in each (after raw-array read, before sort/group/limit).

---

## 3. Sequence Flows

### 3.1 Soft archive (default trash-icon click)
```
User clicks 🗑 → deleteX(id) → K2Archive.archive(kind, id)
  → item.archived = true; item.archivedAt = now
  → KINDS[kind].render()           ← item gone from native page
  → renderTrash() + renderTrashBadge()
  → await saveData()
  → toast({ label: "X archived: <name>", undo: () => restore })
    └─ on Undo (within 8s): item.archived = false; saveData(); re-render
    └─ on expire: nothing further; item stays archived
```

### 3.2 Hard delete (shift+click trash)
```
User shift+clicks 🗑 → deleteX(id, { hard:true }) → K2Archive.archive(kind, id, {hard:true})
  → item.archived = true; archivedHard = true; archivedAt = now
  → KINDS[kind].render() + renderTrash() + renderTrashBadge()
  → await saveData()
  → setTimeout 8000ms (timerKey = `${kind}:${id}`):
      → splice item from DATA[arr]
      → await saveData()
      → renderTrash() + renderTrashBadge()
  → toast({ label: "X deleted: <name>", undo: () => clearTimer + restore })
    └─ on Undo: clearTimeout, unset archived/hard, saveData, re-render
    └─ on expire: toast disappears; timer fires; item gone
```

### 3.3 Restore from Trash page
```
User clicks Restore → K2Archive.restore(kind, id)
  → if _pendingPurge has key → clearTimeout, delete from map
  → unset item.archived/archivedAt/archivedHard
  → await saveData()
  → KINDS[kind].render() + renderTrash() + renderTrashBadge()
```

### 3.4 Empty trash
```
User clicks Empty trash → confirm("permanently delete every archived item?") 
  → for each KIND: DATA[arr] = DATA[arr].filter(notArchived)
  → await saveData()
  → renderTrash() + renderTrashBadge() + every KIND render()
  → toast({ label: "N items purged", undo: null, duration: 3000 })
```

### 3.5 Cmd+K → "Restore most recently archived" [REQ-011]
```
Palette action "Restore last archived":
  → collect all archived items across KINDS, sort by archivedAt desc
  → if empty → toast "Nothing to restore"
  → else → K2Archive.restore(kind, id) on the top one
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

## 5. Failure Modes

| Mode | Behavior |
|---|---|
| `saveData()` fails after archive | Item already marked archived in memory; toast still shows. On next `loadData()`, archive flag is lost (no recovery). [TO VERIFY] — accept this risk for v1. |
| User closes tab mid-undo-window | Item stays archived (or pending-purge); timer dies. On reload, hard-pending items appear in Trash with `archivedHard:true` but no timer running. Trash page treats these as normal archived rows. |
| Two archives in quick succession | Single-toast policy: second toast replaces first; first toast's undo is forfeited. [TO VERIFY] — acceptable per "smooth and clear" goal. |
| Renderer not yet defined when KINDS[k].render() called | `render: () => window.renderX && renderX()` guard. No-op if undefined. |

---

## 6. Open Design Questions (for Phase 0 verification)

1. **Q-1:** Should `dailyDocs` (date-keyed object) support archive? Or treat daily jots as ephemeral by date?
2. **Q-2:** Action Inbox items have a `hidden` field already (existing dismiss flow). Should archive replace `hidden`, coexist, or alias to it?
3. **Q-3:** Should the Cmd+K palette show archived items in search results (with a "(archived)" tag) or hide them entirely?
4. **Q-4:** Does the existing `clips` array live at `DATA.bookmarks` or `DATA.clips`? [Grep verification needed.]
5. **Q-5:** What's the accomplishments renderer function name?
