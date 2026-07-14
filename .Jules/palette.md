## 2026-06-27 - Icon-only buttons lacking ARIA labels
**Learning:** Found widespread lack of `aria-label` attributes on icon-only buttons across the application (e.g. modals, inline action buttons).
**Action:** Always verify icon-only buttons include descriptive `aria-label`s or screen reader only text to ensure functionality is communicated effectively.
## 2024-05-14 - Keyboard traps on custom interactive elements
**Learning:** Adding `role="button"` and `tabindex="0"` to `div` elements makes them focusable, but they will not respond to keyboard events natively like a real `<button>`. If `onkeydown` is not explicitly handled to trigger the click action for 'Enter' and 'Space', keyboard users are trapped and cannot activate the element.
**Action:** Whenever adding button semantics to a `div` or `span`, always include an `onkeydown` handler to listen for 'Enter' and 'Space' (`event.key === ' '`), prevent default scrolling on 'Space', and execute the expected click action.
