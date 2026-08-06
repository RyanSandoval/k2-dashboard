## 2024-07-07 - Inline Debouncing in Single-File Architecture
**Learning:** In a monolithic `index.html` where search inputs directly call heavy DOM-manipulation render functions (e.g. `renderActionInbox()`), attaching inline debounce using `clearTimeout(this.to); this.to = setTimeout(...)` prevents blocking the main thread without the need to manage global debounce closures.
**Action:** Always debounce search/filter inputs that trigger synchronous DOM re-rendering, especially when dealing with large datasets in memory.
