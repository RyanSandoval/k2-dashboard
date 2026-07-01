## 2026-06-27 - Icon-only buttons lacking ARIA labels
**Learning:** Found widespread lack of `aria-label` attributes on icon-only buttons across the application (e.g. modals, inline action buttons).
**Action:** Always verify icon-only buttons include descriptive `aria-label`s or screen reader only text to ensure functionality is communicated effectively.
## 2024-07-01 - Add focus-visible styles for keyboard navigation
**Learning:** Users navigating with keyboards lose track of their position because interactive elements lack distinct focus states due to standard outline-none resets. A global `:focus-visible` rule restores this critical accessibility feature without affecting mouse users.
**Action:** Always include a global `:focus-visible` rule using existing design system colors (like var(--accent)) to ensure focus states are clearly visible for keyboard navigation across all interactive elements.
