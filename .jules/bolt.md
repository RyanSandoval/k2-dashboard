## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2026-09-02 - Unnecessary string manipulation inside high-frequency search loop
**Learning:** The K2Palette search (`refresh()` function) scores every single index item against the search query on every keystroke. Originally, it called `.toLowerCase()` on both the query and the item's label *inside* the scoring loop. Because there can be thousands of items (notes, tasks, projects) and this happens synchronously on keystrokes, repeated string allocation blocked the main thread.
**Action:** When optimizing search or filtering functions in `index.html`, compute and cache pre-lowercased strings during the index building phase (e.g., as `labelLower`) rather than converting strings dynamically inside the scoring loop to prevent repeated string allocations and main-thread blocking on every keystroke.
