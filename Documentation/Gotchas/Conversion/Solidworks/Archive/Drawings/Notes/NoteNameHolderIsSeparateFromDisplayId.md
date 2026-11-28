# Note name holder is separate from display identity

A fresh note can have a valid display identifier while its public name remains empty. Treating `moNoteData_c.f20` or `moDisplayNote_c.f58` as the callable name gives the wrong public API result.

In the exact 2026 ordinary note route, both registered name APIs reach `moNode::name`, which reads the actual holder at `f18` and its CString at `f08`. A null holder returns a shared empty CString. `moNode::Serialize` preserves a separate `f20` CString. Display insertion allocates `f58` from actual model `fd44`, independently of naming.

Ordinary commit auto-naming requires the actual local data owner to be a detail folder and that folder to resolve the real model. Only then does it obtain a localized basename and allocate a suffix through the separate model `f90` name manager. Its map-miss path scans the real owner graph, so an empty counter map cannot be replaced with a guessed zero counter.

Preserve an authored name through the actual typed `f18` holder, or implement the positively bound ordinary owner/name allocation rule. Keep basename localization and unproved scan edge cases explicit. Do not copy an observed English name or derive one from a display id. See the [source ledger](../../../../../../../re/solidworks/records/DrawingPlainNoteNameOwners2026.md) and its sanitized static receipt; they establish no new native or public admission.
