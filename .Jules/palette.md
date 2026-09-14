## 2024-05-24 - Interactive DIVs and Icon-Only Buttons lacking accessibility attributes
**Learning:** Found multiple interactive `div` elements functioning as buttons (like `search-trigger`, `forceAppRefresh`, `openSettings`) that were lacking keyboard accessibility attributes (`role="button"`, `tabindex="0"`, `aria-label`). Additionally, many icon-only buttons in the TipTap floating/selection toolbars were missing `aria-label` attributes, making them inaccessible to screen readers.
**Action:** Always ensure that interactive elements acting as buttons use `<button>` tags when possible, or include `role="button"`, `tabindex="0"`, and `aria-label` if a `<div>` or `<span>` must be used. Also, ensure all icon-only buttons have an `aria-label` describing their action.

## 2024-05-24 - Interactive DIVs missing keyboard handlers
**Learning:** Adding `role="button"`, `tabindex="0"`, and `aria-label` to a `div` element makes it discoverable by screen readers and focusable via keyboard, but it does *not* automatically map the `Enter` or `Space` key to trigger the `onclick` handler. This creates a keyboard trap where elements can be focused but not activated.
**Action:** When converting `div` elements to buttons (instead of using native `<button>` tags), ensure an `onkeydown` event listener is also added to map `Enter` and `Space` keys to the click action.
## 2024-08-17 - Added aria-labels to orphaned inputs
**Learning:** Found a pattern of orphaned search/capture input fields without labels in index.html (relying solely on placeholders). Placeholders are insufficient for screen readers as accessible names.
**Action:** When adding new inputs, always include a corresponding `<label>` element or, if visually hidden, an `aria-label` attribute.
## 2024-11-20 - Added aria-label to command palette search input
**Learning:** Found an orphaned search input field inside the command palette (`k2pal-input`) relying only on its placeholder attribute. For screen readers, an `aria-label` is required for context when a visible `<label>` is not present.
**Action:** When adding new search inputs or modifying existing ones without explicit labels, always ensure an `aria-label` attribute is added for accessibility.
