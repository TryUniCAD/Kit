# A valid principal plane ID can carry a conflicting basis

A resolved-feature handle stores the referenced plane ID and an
independent axis kind and basis. The ID can name an existing principal
plane while the frame belongs to a different plane.

Strict opening rejects this conflict. Permissive opening keeps the
sketch with an unresolved attachment and reports the rejected ID.
Preserve that status and omit typed support-reference provenance.
A framed inspection fallback cannot qualify the sketch for export.
[Reader evidence](../../../../../re/solidworks/records/AggregateReaderRepairs2026.md)
