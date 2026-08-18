## 2024-05-24 - Interactive DIVs and Icon-Only Buttons lacking accessibility attributes
**Learning:** Found multiple interactive `div` elements functioning as buttons (like `search-trigger`, `forceAppRefresh`, `openSettings`) that were lacking keyboard accessibility attributes (`role="button"`, `tabindex="0"`, `aria-label`). Additionally, many icon-only buttons in the TipTap floating/selection toolbars were missing `aria-label` attributes, making them inaccessible to screen readers.
**Action:** Always ensure that interactive elements acting as buttons use `<button>` tags when possible, or include `role="button"`, `tabindex="0"`, and `aria-label` if a `<div>` or `<span>` must be used. Also, ensure all icon-only buttons have an `aria-label` describing their action.

## 2024-05-24 - Interactive DIVs missing keyboard handlers
**Learning:** Adding `role="button"`, `tabindex="0"`, and `aria-label` to a `div` element makes it discoverable by screen readers and focusable via keyboard, but it does *not* automatically map the `Enter` or `Space` key to trigger the `onclick` handler. This creates a keyboard trap where elements can be focused but not activated.
**Action:** When converting `div` elements to buttons (instead of using native `<button>` tags), ensure an `onkeydown` event listener is also added to map `Enter` and `Space` keys to the click action.

## 2024-05-24 - Unlabeled inputs and checkboxes require aria-labels
**Learning:** Found multiple `<input>` elements (text inputs, checkboxes, and date pickers) throughout the application that lacked associated text labels or `<label for="...">` tags. This pattern included dynamically generated checkboxes in TipTap tasks, project spec toggles, review steps, and date inputs for tasks and slash commands. Without these labels, screen reader users cannot understand the purpose of the inputs.
**Action:** When creating form inputs or interactive checkboxes that do not have explicitly associated text, always ensure an `aria-label` attribute is added to provide a descriptive accessible name for screen readers.
