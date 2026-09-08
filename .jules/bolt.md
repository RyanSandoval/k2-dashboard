## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.
## 2026-09-08 - Command Palette Search Caching
**Learning:** In hot loops like the command palette search which triggers on every keystroke, dynamic string manipulation (like `.toLowerCase()`) on hundreds of items blocks the main thread and degrades responsiveness.
**Action:** Always compute and cache invariant transformations (like lowercased labels) during the index-building phase or initialization, rather than doing it dynamically in scoring loops.
