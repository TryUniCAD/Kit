# Cylinder optional axis needs its own state

A faceted support snapshot and its surrounding cylindrical reference wrapper have different owners. The wrapper's `f108` is not another snapshot field or a second world-axis copy.

The actual 2026 wrapper constructor leaves a private optional state null. Concrete wrapper virtual `+0x328` can enable it by allocating from the current world cylinder and actual occurrence transform, or clear it. The current store writes only the state's local unit vector, behind its own presence word. All twelve disclosed active references contain that vector, while their detached support wrappers do not. A rotated disclosed case distinguishes the local vector from the world axis.

Construct the snapshot from its actual face/body roles and model any optional orientation operation separately. Do not infer the active enabling caller from repeated presence, copy `-Z` from a sample, or claim that a later geometry update preserves the state unconditionally. The concrete enabling caller and fresh native acceptance remain open.

[Exact ownership, operation and serializer evidence](../../../../../../re/solidworks/records/ConcentricSupportSnapshotConstruction2026.md)
