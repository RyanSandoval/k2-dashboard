## 2025-02-18 - Missing debounce on search inputs
**Learning:** Frequent events like `oninput` can trigger expensive DOM rendering operations (e.g., `renderNotes`, `renderActionInbox`, `renderDailyDocs`) repeatedly, leading to unresponsiveness.
**Action:** Implement a generic `debounce` function and use it for all search inputs that cause expensive list re-renders.
