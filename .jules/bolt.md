## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.
## 2026-07-04 - Repeated String Allocations in Search Filtering
**Learning:** During Command Palette fuzzy-search, converting search items and the query to lowercase inside the inner scoring loop (e.g., `O(N * M)` allocations per keystroke) causes rapid memory allocations and garbage collection overhead, leading to search stuttering in large datasets.
**Action:** When optimizing search or filtering functions in `index.html`, compute and cache pre-lowercased strings during the index building phase (e.g., as `labelLower`) rather than converting strings dynamically inside the scoring loop to prevent repeated string allocations and main-thread blocking on every keystroke.
