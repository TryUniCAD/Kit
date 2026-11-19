# Cylinder optional axis needs its own state

A faceted support snapshot holds the selected face and body identities. Its surrounding cylindrical reference wrapper owns a separate `f108` orientation state containing the local axis.

The actual 2026 wrapper constructor leaves a private optional state null. Concrete wrapper virtual `+0x328` can enable it by allocating from the current world cylinder and actual occurrence transform, or clear it. The current store writes only the state's local unit vector, behind its own presence word. All twelve disclosed active references contain that vector, while their detached support wrappers do not. A rotated disclosed case distinguishes the local vector from the world axis.

Construct the snapshot from its actual face and body roles. The native selected-face factory explicitly enables the local-axis state using the occurrence transform. The cold-open refresh and native acceptance remain open. [Native enable caller](../../../../../../re/solidworks/records/ConcentricOrientationEnable2026.md)

[Exact ownership, operation and serializer evidence](../../../../../../re/solidworks/records/ConcentricSupportSnapshotConstruction2026.md)
