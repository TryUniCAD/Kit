# A saved keyword sibling order can depend on a display address

SOLIDWORKS 2026 uses an allocated display object's low address word in
a dimension map key when its actual parameter has node ID `-1`. Seven
saved parts have a different sibling order with the same display values
as their binary model lists.

Join dimension identity to the owning parameter and active display
selection. Use the modeled presentation sequence during construction.
Retain the typed source sequence when checking exact saved stream replay.
[Native and archive evidence](../../../../../../re/solidworks/records/KeywordOwnerProjection2026.md)
