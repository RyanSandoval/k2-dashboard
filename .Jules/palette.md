## 2026-06-27 - Icon-only buttons lacking ARIA labels
**Learning:** Found widespread lack of `aria-label` attributes on icon-only buttons across the application (e.g. modals, inline action buttons).
**Action:** Always verify icon-only buttons include descriptive `aria-label`s or screen reader only text to ensure functionality is communicated effectively.
## 2024-07-08 - Keyboard Accessibility for Interactive Divs
**Learning:** In the K-2 dashboard, several interactive elements (like the sidebar footer actions for refresh and settings) were implemented using `div` tags with `onclick` handlers, but lacked keyboard accessibility attributes. This causes issues for screen reader users and those navigating via keyboard.
**Action:** When using `div` or `span` as interactive elements, always ensure they include `role="button"`, `tabindex="0"`, an appropriate `aria-label`, and an `onkeydown` handler that maps the 'Enter' and 'Space' keys to the click action.
