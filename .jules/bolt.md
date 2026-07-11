## 2024-05-24 - Debouncing inline event handlers in a monolithic HTML file
**Learning:** Monolithic `index.html` files with inline `oninput` handlers calling synchronous render functions directly cause performance bottlenecks by blocking the main thread on every keystroke.
**Action:** Use the inline debouncing pattern `oninput="clearTimeout(this.to); this.to = setTimeout(() => functionName(), delay)"` to prevent global scope pollution and main thread blocking without requiring external utility functions.
