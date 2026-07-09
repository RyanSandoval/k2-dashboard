## 2024-06-25 - Debounce Inline Handlers
**Learning:** Adding debouncing directly to inline `oninput` handlers prevents frequent main thread blocking and unnecessary rapid layout/script execution for inputs that trigger complex filtering or rendering in this single-page dashboard.
**Action:** Use `oninput="clearTimeout(this.to); this.to = setTimeout(() => myFunction(), 250)"` pattern for search and text inputs instead of creating separate utility functions when working within monolithic index.html file.
