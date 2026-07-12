## 2023-10-27 - Inline debounce for search handlers
**Learning:** Found multiple search/filter fields using synchronous `oninput` handlers which triggered expensive rendering logic, potentially causing main-thread blocking during rapid typing.
**Action:** When working with inline event handlers in a vanilla JS setup without an external debounce utility, utilize the `clearTimeout(this.to); this.to = setTimeout(...)` pattern on the DOM node itself to easily scope and apply debouncing logic without polluting the global space.
