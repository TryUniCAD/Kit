# SOLIDWORKS partition mark identities

`ReadHistMarks` returns the selected mark ID and immediate predecessor ID
from a validated Parasolid delta payload. Zero represents an absent predecessor.
The reader uses the existing version-3701250 profile and checks the active
world, referenced marks, rollback ownership, and stream termination.
`ReadXmtHistory` uses the same reader and returns `None` after validation.
[Archive entry point](../../../../src/convert/adapters/solidworks/Archive/Partition/ReadHistMarks.py)

Disclosed SOLIDWORKS 2026 part controls returned `(7, 3)` and `(3, 2)`.
An independently authored initial mark returned `(1, 0)`. Five malformed
or detached inputs preserved their previous refusals. A current alternate
layout and a prior schema retained their public geometry while their deltas
triggered the bounded reader's existing refusals.
[Guarded process evidence](../../../../re/solidworks/records/PartitionMarkIds2026.md)

This archive change covers mark extraction. Feature ownership, new schema
support, and conversion acceptance require separate evidence.
[Adapter reference](../../../Reference/Adapters/Solidworks.md)
