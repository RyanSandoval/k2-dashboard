## 2026-09-06 - Cached Pre-lowercased Strings in Palette Search
**Learning:** When optimizing search or filtering functions in index.html (like K2 Palette search), repeatedly calling `.toLowerCase()` on the haystack strings dynamically inside the scoring loop causes redundant string allocations and main-thread blocking on every keystroke.
**Action:** Compute and cache pre-lowercased strings during the index building phase (e.g., as `labelLower`), and pass these directly to the scoring function to prevent blocking the main thread during user input.
