## 2024-07-13 - Debouncing Inline Event Handlers in Monolithic Structure
**Learning:** In a monolithic architecture like K-2 where most logic is embedded directly in `index.html`, missing debouncing on inline event handlers (like `oninput` for searches) can cause severe main-thread blocking due to rapid, synchronous re-renders during fast typing.
**Action:** Use the pattern `oninput="clearTimeout(this.to); this.to = setTimeout(() => functionName(), delay)"` to provide immediate inline debouncing without polluting global scope or requiring external utility functions.
