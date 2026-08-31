## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2026-08-30 - Prevent per-keystroke string allocations in search loops
**Learning:** High-frequency rendering and filtering loops (like Command Palette search scoring) that convert strings via `.toLowerCase()` on every execution cause heavy main-thread garbage collection thrashing, slowing down perceived input latency.
**Action:** Always pre-compute and store `.toLowerCase()` versions of strings during the index-building phase so the high-frequency scoring loop only performs raw string comparisons without allocating new memory.
