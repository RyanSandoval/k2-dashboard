## 2026-06-27 - Icon-only buttons lacking ARIA labels
**Learning:** Found widespread lack of `aria-label` attributes on icon-only buttons across the application (e.g. modals, inline action buttons).
**Action:** Always verify icon-only buttons include descriptive `aria-label`s or screen reader only text to ensure functionality is communicated effectively.
## 2026-06-27 - Search inputs lacking ARIA labels
**Learning:** Found widespread lack of `aria-label` attributes on inputs used for searching that only use `placeholder` text instead of visual labels.
**Action:** Always verify search inputs or inputs without visible `<label>` elements include descriptive `aria-label`s to ensure the purpose is communicated to screen readers.
