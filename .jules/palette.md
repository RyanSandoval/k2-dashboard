
## 2024-05-24 - Connect `<label>` and `<input>`/`<select>` in modals
**Learning:** Custom UI modals missing explicit `for` attributes on form labels prevent click-to-focus and hinder screen reader accessibility.
**Action:** When adding or modifying form fields, particularly in custom UI modals, always explicitly link the `<label>` to its corresponding input element (e.g., `<input>`, `<select>`, `<textarea>`) using matching `for` and `id` attributes. This ensures click-to-focus functionality and robust screen reader accessibility.
