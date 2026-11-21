# Strict reading of canonical generated blank drawings

The strict drawing reader now has a bounded path for one generated, unlinked ANSI A landscape sheet. It recovers the actual typed sheet and all native presentation/provenance inputs, regenerates the seven logical streams and the whole container, and refuses any unrepresented source state. The complete reconstructed semantic input remains in source attributes and survives public JSON serialization.

Use ordinary `open_document(..., source_format="solidworks.slddrw", strict=True)` for that profile. Existing partial inspection remains available with its warning. Native D00, native-saved derivatives, linked views, annotations, extra properties and noncanonical framing remain refused by this strict path. The public writer still rejects the preserved native attributes; this entry does not claim public read-to-write support.

Seventy-two isolated SDK processes pass 36 paired groups with six positive and eighteen rejection files. Partial output is unchanged, audited extra input/process access is zero, and internal typed destination/save repeats preserve all other owners. No native oracle or original private source was opened. [Scope and field ownership](../../../../../../re/solidworks/records/SdkGeneratedBlankStrictReader2026.md) [Exact receipt](../../../../../../re/solidworks/measurements/2026/SdkGeneratedBlankStrictRead01.json)
