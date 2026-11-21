# Creation-log names follow active document construction

The empty CString in `moLogs_c` constructors is an initial seed, not a rule that
every saved creation log must have an empty name. Rejecting an authored document
name omits a later native constructor assignment.

Static 2026 analysis finds that active filed-concept construction at
`sldmodu.dll!0x4bda5a20` creates and attaches the creation log, then assigns the
authored document name to log member `+0x50`. In
`sldarchiveu.dll!0x31a04830`, the store path loads the log identifier at
`0x31a0485b`, addresses the string at `0x31a04864`, and tail-calls the CString
writer at `0x31a0487a`. The load path addresses the same member at
`0x31a04890` and calls the CString reader at `0x31a0489a`. Neither path substitutes
an empty string.

The inspected `sldmodu.dll` SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`;
`sldarchiveu.dll` is
`5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48`.
This evidence is static constructor and serializer dataflow, not a runtime trace
or a value inferred from related saved designs.

Pass the neutral document's authored name explicitly in its creation-log
mapping. Keep later log names explicit until their owning operation is known.
Do not copy saved metadata or infer vendor provenance from a document name.
The [metadata reference](../../../../../re/solidworks/records/MetadataConstruction2026.md)
documents the builder interface and remaining restrictions.
