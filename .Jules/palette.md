## 2026-06-27 - Icon-only buttons lacking ARIA labels
**Learning:** Found widespread lack of `aria-label` attributes on icon-only buttons across the application (e.g. modals, inline action buttons).
**Action:** Always verify icon-only buttons include descriptive `aria-label`s or screen reader only text to ensure functionality is communicated effectively.

## 2026-07-10 - Custom Interactive Elements Keyboard Accessibility
**Learning:** Custom interactive `div` and `span` elements acting as buttons (e.g., `.search-trigger`) in this application often lack essential keyboard accessibility attributes. Specifically, they have `onclick` handlers but are missing `role="button"`, `tabindex="0"`, and `:focus-visible` styling, creating keyboard traps or dead ends for non-mouse users.
**Action:** When identifying custom interactive elements with `onclick`, always ensure they are fully keyboard accessible by adding `role="button"`, `tabindex="0"`, a keyboard event handler (`onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();this.click();}"`), and `:focus-visible` styles that mirror hover states with `outline: none;` to maintain consistent visual feedback.
