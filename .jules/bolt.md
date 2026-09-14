## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2026-09-03 - Repeated string allocation in K2Palette
**Learning:** Dynamic generation of `toLowerCase()` inside tight scoring loops across all items in a large array (Tasks, Notes, Projects, etc) causes a substantial amount of repeated string allocation, which leads to unnecessary garbage collection pauses and main-thread blocking on every search keystroke in the command palette.
**Action:** Always pre-compute and cache expensive immutable string conversions (like `labelLower`) at the index creation phase, and only call `toLowerCase()` on the dynamic user query exactly once outside of the iteration loop before passing it in.
