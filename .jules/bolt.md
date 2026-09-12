## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2026-09-12 - Pre-compute toLowerCase for K2Palette Search
**Learning:** In the K2Palette's search scoring loop, dynamically calling `.toLowerCase()` on the haystack and needle inside the `score` function blocks the main thread because it repeatedly allocates strings for every item evaluated on every keystroke. This causes performance degradation and lag during typing in the search bar.
**Action:** Always pre-compute and cache `.toLowerCase()` strings during the index building phase (e.g., as `labelLower`), and compute the lowercase query string exactly once outside the search loop, to avoid repeated allocations and improve responsiveness.
