## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2026-09-09 - Redundant lowercasing inside search loops
**Learning:** Calling `toLowerCase()` dynamically on both the needle and the haystack inside a scoring loop for every keystroke over every indexed item causes thousands of redundant string allocations, leading to unnecessary garbage collection pauses and main-thread blocking during search.
**Action:** Always pre-compute and cache the lowercased strings during index creation (e.g., `labelLower`), and perform `toLowerCase()` on the search query exactly once before entering the scoring loop.
