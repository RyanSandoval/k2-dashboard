## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2026-09-01 - Repeated string allocations in search filter
**Learning:** The command palette (`refresh()`) dynamically converted strings to lowercase inside a `.map()` block for every search result item on every keystroke, which creates performance overhead from GC pressure and string allocations.
**Action:** When filtering/scoring large sets on user input, pre-compute lowercased properties during index creation so the scoring loop only performs fast comparisons.
