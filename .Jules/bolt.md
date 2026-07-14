## 2024-05-18 - Debounce Search Inputs
**Learning:** `oninput` handlers without debouncing block the main thread and slow down the app.
**Action:** Always wrap search input handlers with `setTimeout` debouncing in monoliths.
