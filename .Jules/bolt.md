
## 2023-10-27 - Optimize Launcher Search Filtering
**Learning:** High-frequency event handlers (like `oninput` for search) are easily bottlenecked by synchronous DOM operations (e.g., `querySelector`, `textContent`) and repeated string allocations (`toLowerCase()`) inside filtering loops.
**Action:** When filtering UI lists based on text, pre-compute the search string into a data attribute (like `data-search="lowercase label"`) during the rendering phase. This allows the filter function to simply read `dataset.search` rather than allocating strings and querying the DOM on every keystroke.
