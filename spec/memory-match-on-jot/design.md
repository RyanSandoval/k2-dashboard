🧠 memory-match-on-jot

# Design — K2 Memory Match on New Jot

**Version:** v0.1 (2026-06-21)
**Implements:** requirements.md REQ-001 through REQ-012

---

## Architecture

Pure client-side. No new cron, no API call, no build step. All logic lives in `index.html` as new functions + a small HTML addition. Touches: one `<div>` insertion in the jots page HTML, one hook in `_createTodayEditor.onUpdate`, three new functions.

```
_createTodayEditor.onUpdate
  └── debouncedMemoryMatch()          ← new, debounced 1500ms
        └── _runMemoryMatch()
              ├── strip HTML → plain text, check min length (REQ-002)
              ├── _memTokenize(text) → Set<string>  (REQ-005)
              ├── build candidates from DATA.notes + DATA.dailyDocs (REQ-003, REQ-004)
              ├── score each → _memMatchScore(jotTerms, candTerms) (REQ-005)
              ├── find top match (REQ-006)
              └── renderJotMatchNudge(match | null)  (REQ-007, REQ-008, REQ-009)
```

---

## Data Structures

No new DATA fields. All state is ephemeral window-level:

```js
window._memMatchDismissed  // bool — user tapped × on last nudge
window._memMatchLastId     // string — id/date of last shown match (for dismiss reset logic)
window._memMatchTimer      // setTimeout handle for debounce
```

---

## New Functions

### `_memTokenize(text) → Set<string>`
```
1. text.toLowerCase()
2. replace /[^a-z0-9\s]/g with ' '
3. split on whitespace
4. filter: length >= 3, not in STOPLIST
5. return new Set(tokens)
```

Stoplist (~50 words): `a, an, the, and, or, but, in, on, at, to, for, of, with, by, from, up, about, into, then, than, that, this, these, those, is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, could, should, may, might, can, not, no, i, me, my, we, our, you, your, it, its, he, she, they, them, we`.

### `_memMatchScore(setA, setB) → number`
```
intersection = |{x : x in A and x in B}|
union        = |A| + |B| - intersection
return intersection / union  (0 if union === 0)
```
Both args are `Set<string>` from `_memTokenize`.

### `_runMemoryMatch()`
```
1. Get today's HTML from window._todayEditor.getHTML()
2. Strip tags → plain text
3. If plain text < 25 chars → renderJotMatchNudge(null); return
4. jotTerms = _memTokenize(plain text)
5. Build candidates:
   a. DATA.notes.filter(n => !n.archived).map(n => ({
        kind: 'note', id: n.id,
        title: n.title || _firstLine(n.text) || 'Untitled',
        text: (n.title + ' ' + n.text).replace(/<[^>]+>/g,''),
        date: n.created
      }))
   b. Object.entries(DATA.dailyDocs || {})
        .filter(([d]) => d !== window._todayEditorDate)
        .sort(([a],[b]) => b.localeCompare(a))
        .slice(0, 30)
        .map(([date, doc]) => ({
          kind: 'doc', id: date,
          title: _fmtDocDate(date),
          text: (doc.content || '').replace(/<[^>]+>/g,''),
          date
        }))
6. Score each candidate: _memMatchScore(jotTerms, _memTokenize(cand.text))
7. topMatch = candidate with highest score where score >= 0.12
8. If window._memMatchDismissed && topMatch?.id === window._memMatchLastId → return (stay hidden)
9. If topMatch?.id !== window._memMatchLastId → clear _memMatchDismissed
10. renderJotMatchNudge(topMatch || null)
```

### `renderJotMatchNudge(match)`
```
const el = document.getElementById('jot-match-nudge')
if (!match) { el.style.display = 'none'; return }

window._memMatchLastId = match.id
const snippet = match.text.replace(/\s+/g, ' ').trim().slice(0, 80)
el.innerHTML = `
  <span style="...icon style...">📎</span>
  <span style="...label...">Prior note match</span>
  <span style="...title..."><strong>${escapeHtml(match.title)}</strong> · ${escapeHtml(match.date?.slice(0,10)||'')}</span>
  <span style="...snippet...">${escapeHtml(snippet)}…</span>
  <button onclick="_memMatchNavigate('${escapeAttr(match.kind)}','${escapeAttr(match.id)}')" style="...">Compare →</button>
  <button onclick="_memMatchDismiss()" style="...">×</button>
`
el.style.display = 'flex'
```

### `_memMatchNavigate(kind, id)`
```
if kind === 'note':   openNoteEditor(id)
if kind === 'doc':    navigateTo('jots'); _memMatchExpandDoc(id)
```

### `_memMatchExpandDoc(date)`
```
const el = document.querySelector(`.jot-day-header[data-date="${date}"]`)
if (el && !window._openDocDays.has(date)) toggleDocDay(el)
el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
```

### `_memMatchDismiss()`
```
window._memMatchDismissed = true
document.getElementById('jot-match-nudge').style.display = 'none'
```

---

## HTML Change

Insert once, immediately after `#daily-doc-today-editor` in the jots page:

```html
<div id="jot-match-nudge"
  style="display:none;align-items:center;gap:8px;flex-wrap:wrap;
         padding:8px 12px;margin-top:6px;
         background:color-mix(in srgb,var(--accent) 10%,transparent);
         border:1px solid var(--accent-dim);
         border-radius:var(--radius-sm);font-size:12px;color:var(--text-dim);
         line-height:1.4;">
</div>
```

---

## Hook in `_createTodayEditor`

In the `onUpdate` handler, after the existing `debouncedJotLinker()` call:

```js
if (!isCheckboxToggle && typeof window.debouncedMemoryMatch === 'function') {
  window.debouncedMemoryMatch();
}
```

And define once, near `debouncedJotLinker`:

```js
window.debouncedMemoryMatch = (function() {
  let t = null;
  return function() {
    clearTimeout(t);
    t = setTimeout(_runMemoryMatch, 1500);
  };
})();
```

---

## Performance

Worst case: 200 notes × avg 200 tokens → tokenize each = O(200 × 200) = 40k ops. Plus 30 docs × 300 tokens = 9k ops. Total ~50k Set operations. Benchmark: ~5-15ms on M-series. Well inside the 100ms guard (REQ-012).

Pre-tokenizing the corpus on data load is not needed for MVP but is a simple Phase 2 optimization if notes grow past 500.

---

## Files Changed

| File | Change |
|------|--------|
| `index.html` | Add `#jot-match-nudge` div in jots page HTML (1 line) |
| `index.html` | Add `_memTokenize`, `_memMatchScore`, `_runMemoryMatch`, `renderJotMatchNudge`, `_memMatchNavigate`, `_memMatchExpandDoc`, `_memMatchDismiss` (6 functions, ~80 lines) |
| `index.html` | Add `debouncedMemoryMatch` debounce wrapper (~6 lines) |
| `index.html` | Hook `debouncedMemoryMatch()` in `_createTodayEditor.onUpdate` (1 line) |

No new files. No new crons. No new data keys in `DATA`.
