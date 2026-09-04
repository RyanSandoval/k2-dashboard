## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2024-05-18 - Pre-computing Search Strings
**Learning:** Running string lowercasing inside high-frequency filter loops causes unnecessary main-thread blocking and garbage collection, especially on large lists.
**Action:** Compute and cache lowercased strings in data attributes (e.g. `data-search`) during DOM generation, and use these pre-computed attributes in filter loops.
