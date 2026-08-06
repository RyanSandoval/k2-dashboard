## 2026-06-28 - [Optimize K2Palette Search]
**Learning:** The K2Palette command palette rebuilt its entire search index (iterating through all notes, tasks, projects, etc.) on every single keystroke during `refresh()`, causing unnecessary main thread overhead and potential input lag.
**Action:** Cache the search index during the `open()` call and clear it during `close()`, using the cached version in `refresh()`.
