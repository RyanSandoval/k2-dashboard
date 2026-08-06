## 2026-06-27 - Icon-only buttons lacking ARIA labels
**Learning:** Found widespread lack of `aria-label` attributes on icon-only buttons across the application (e.g. modals, inline action buttons).
**Action:** Always verify icon-only buttons include descriptive `aria-label`s or screen reader only text to ensure functionality is communicated effectively.
## 2024-05-18 - Keyboard Accessibility for Clickable Divs
**Learning:** The application extensively uses `div` elements with `onclick` handlers for navigation and interactive triggers without corresponding keyboard events or semantic roles.
**Action:** When discovering interactive `div` elements without native semantics, always add `role="button"`, `tabindex="0"`, and map 'Enter'/'Space' to the `onclick` action via an `onkeydown` handler to ensure keyboard accessibility, avoiding keyboard traps.
