## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2026-07-15 - Debouncing command palettes breaks fast type-and-commit flows
**Learning:** Debouncing a command palette search input creates a race condition where hitting 'Enter' immediately after typing activates the result from the *previous* query, breaking the core fast-action flow. Furthermore, simple string fuzzy-matching over ~1,000 items takes sub-millisecond time and doesn't block the main thread, unlike complex view generation.
**Action:** Never debounce command palette or fast-action search inputs. If search latency becomes a real issue, optimize the scoring loop (e.g., caching lowercased strings) instead of adding input delay.
