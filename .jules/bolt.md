## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.
## 2025-02-18 - Pre-compute and Cache Lowercase Strings for Search
**Learning:** In heavily used search or filtering functions (like the K2Palette modal), repeatedly calling `.toLowerCase()` on the same strings during the scoring loop on every keystroke causes unnecessary string allocations and can block the main thread.
**Action:** Compute and cache pre-lowercased strings (e.g., `labelLower`) during the index building phase, and convert the search query to lowercase only once per keystroke, rather than converting strings dynamically inside the scoring loop.
