## 2026-07-04 - Unnecessary rendering on keystroke
**Learning:** High frequency events like search keystrokes run complex view generation and UI redraw routines (`renderActionInbox`, `renderNotes`, etc) directly on every keystroke, causing noticeable UI stuttering.
**Action:** Always wrap high-frequency search input event handlers with a debounce wrapper (`debounce(fn, 250)`) to ensure the main thread isn't blocked on every character input.

## 2026-07-04 - Cache string conversions in DOM for high-frequency filtering
**Learning:** High-frequency filtering loops (like the command launcher search) can suffer from repeated string allocations and DOM querying () on every keystroke. Using  caching doesn't just save time, it fundamentally changes the performance profile of the loop from DOM-bound to memory-bound.
**Action:** When optimizing client-side search/filtering over many DOM elements, compute and inject pre-lowercased search strings into  attributes during the initial render phase rather than converting them dynamically inside the filtering loop.

## 2026-07-04 - Cache string conversions in DOM for high-frequency filtering
**Learning:** High-frequency filtering loops (like the command launcher search) can suffer from repeated string allocations and DOM querying (`tile.querySelector('.tile-nm')?.textContent.toLowerCase()`) on every keystroke. Using `dataset` caching doesn't just save time, it fundamentally changes the performance profile of the loop from DOM-bound to memory-bound.
**Action:** When optimizing client-side search/filtering over many DOM elements, compute and inject pre-lowercased search strings into `data-search` attributes during the initial render phase rather than converting them dynamically inside the filtering loop.
