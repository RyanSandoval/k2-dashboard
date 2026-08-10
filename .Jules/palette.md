## 2024-05-24 - Interactive DIVs and Icon-Only Buttons lacking accessibility attributes
**Learning:** Found multiple interactive `div` elements functioning as buttons (like `search-trigger`, `forceAppRefresh`, `openSettings`) that were lacking keyboard accessibility attributes (`role="button"`, `tabindex="0"`, `aria-label`). Additionally, many icon-only buttons in the TipTap floating/selection toolbars were missing `aria-label` attributes, making them inaccessible to screen readers.
**Action:** Always ensure that interactive elements acting as buttons use `<button>` tags when possible, or include `role="button"`, `tabindex="0"`, and `aria-label` if a `<div>` or `<span>` must be used. Also, ensure all icon-only buttons have an `aria-label` describing their action.

## 2024-05-24 - Interactive DIVs missing keyboard handlers
**Learning:** Adding `role="button"`, `tabindex="0"`, and `aria-label` to a `div` element makes it discoverable by screen readers and focusable via keyboard, but it does *not* automatically map the `Enter` or `Space` key to trigger the `onclick` handler. This creates a keyboard trap where elements can be focused but not activated.
**Action:** When converting `div` elements to buttons (instead of using native `<button>` tags), ensure an `onkeydown` event listener is also added to map `Enter` and `Space` keys to the click action.

## 2025-02-18 - Interactive DIVs missing keyboard accessibility (Sidebar Nav)
**Learning:** The `nav-section-title` elements in the sidebar acting as accordions (Work, Reference) were created as standard `div` tags with `onclick` handlers. Without `role="button"`, `tabindex="0"`, `aria-label`, and `onkeydown` listeners, they were completely invisible to screen readers and impossible to navigate to via keyboard.
**Action:** Always ensure that interactive structural elements (like accordions or section headers that toggle content) receive full keyboard accessibility attributes, particularly the `onkeydown` handler to allow 'Enter' and 'Space' activation.
