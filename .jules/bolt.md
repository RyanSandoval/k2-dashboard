## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2025-02-18 - Avoid repeated string allocations in K2Palette search
**Learning:** During optimization of the K2Palette global search modal (`Cmd+K`), it was discovered that string `toLowerCase()` conversions were repeatedly dynamically computed inside the scoring loop on every keystroke, causing unnecessary string allocations and potentially blocking the main thread.
**Action:** When building search or filtering indexes in `index.html`, compute and cache pre-lowercased strings (e.g., `labelLower`) at the initialization/build phase so that during the active keystroke event loop, only a single `.toLowerCase()` query is needed, which significantly optimizes the inner fuzzy scoring logic.
