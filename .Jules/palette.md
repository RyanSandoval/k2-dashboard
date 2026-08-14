## 2024-05-24 - Interactive DIVs and Icon-Only Buttons lacking accessibility attributes
**Learning:** Found multiple interactive `div` elements functioning as buttons (like `search-trigger`, `forceAppRefresh`, `openSettings`) that were lacking keyboard accessibility attributes (`role="button"`, `tabindex="0"`, `aria-label`). Additionally, many icon-only buttons in the TipTap floating/selection toolbars were missing `aria-label` attributes, making them inaccessible to screen readers.
**Action:** Always ensure that interactive elements acting as buttons use `<button>` tags when possible, or include `role="button"`, `tabindex="0"`, and `aria-label` if a `<div>` or `<span>` must be used. Also, ensure all icon-only buttons have an `aria-label` describing their action.

## 2024-05-24 - Interactive DIVs missing keyboard handlers
**Learning:** Adding `role="button"`, `tabindex="0"`, and `aria-label` to a `div` element makes it discoverable by screen readers and focusable via keyboard, but it does *not* automatically map the `Enter` or `Space` key to trigger the `onclick` handler. This creates a keyboard trap where elements can be focused but not activated.
**Action:** When converting `div` elements to buttons (instead of using native `<button>` tags), ensure an `onkeydown` event listener is also added to map `Enter` and `Space` keys to the click action.

## 2024-05-24 - Unlabelled/Orphaned Checkboxes
**Learning:** Multiple checkboxes in the application (like the smart list stale task filter or rendered daily jot tasks) lacked explicit accessible names. Some were placed adjacently to `<label>` elements without a `for` attribute linking them, and others were wrapped inside a `<label>` but missing text directly inside the label tag, rendering them "unlabelled" to screen readers.
**Action:** Always ensure checkboxes have an accessible name. Use the `for` attribute on a `<label>` to explicitly link it to a checkbox ID, or provide an `aria-label` directly on the `<input type="checkbox">` if generating a semantic association via `<label>` isn't feasible or the wrapper label is visually empty.
