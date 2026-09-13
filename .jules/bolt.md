## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.
## 2026-07-04 - Unnecessary main thread blocking on launcher search
**Learning:** The K2 launcher search filter (`k2FilterLauncher`) was running synchronously on every keystroke (`oninput`), extracting and lowercasing text content dynamically for all items, causing main-thread blocking and UI stutter.
**Action:** Implemented a generic `debouncedK2FilterLauncher` using `debounce(fn, 250)`. Computed and cached pre-lowercased strings as `data-search` attributes on tool tiles during render, replacing expensive runtime DOM traversal with faster attribute lookups.
