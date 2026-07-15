## 2026-06-27 - Icon-only buttons lacking ARIA labels
**Learning:** Found widespread lack of `aria-label` attributes on icon-only buttons across the application (e.g. modals, inline action buttons).
**Action:** Always verify icon-only buttons include descriptive `aria-label`s or screen reader only text to ensure functionality is communicated effectively.

## 2024-06-25 - Interactive Span Accessibility
**Learning:** In a monolithic HTML setup where elements like `span` or `div` are used as buttons (e.g., the shortcuts toggle), they lack built-in keyboard accessibility. Adding `role="button"` and `tabindex="0"` makes them focusable, but an `onkeydown` handler mapping 'Enter' and 'Space' to the click action is required to avoid keyboard traps. `event.preventDefault()` must be used to prevent default page scrolling when pressing 'Space'.
**Action:** Always add the full suite of ARIA attributes (`role`, `tabindex`, `aria-label`) and an `onkeydown` handler (handling 'Enter' and 'Space' with `preventDefault()`) when making non-interactive elements behave like buttons.
