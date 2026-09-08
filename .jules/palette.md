
## 2024-09-08 - Added explicit for attributes to modal form labels
**Learning:** In custom UI modals, form labels are frequently rendered without `for` attributes linking them to inputs, degrading accessibility and breaking click-to-focus behavior.
**Action:** Always explicitly link `<label>` elements to their corresponding input elements using matching `for` and `id` attributes when building or modifying custom UI modals.
