# The assembly display update follows the header counter

`DLUpdateStamp` follows `f40` in the paired assembly headers.
It can differ between two documents that have the same model
geometry stamp `f1300`. The disclosed aligned locked source
starts at 106 while the aligned free source starts at 105, with
`f1300=102` in both.

Read the complete display update record and join its value to the
actual header update counter. Keep the geometry stamp and its
configuration-directory aggregate separate.
[Measured typed comparison](../../../../../../re/solidworks/records/ConcentricD01StampStreams2026.md)
