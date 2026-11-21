# Note arrowhead storage has an indexed fallback

An empty `moNoteData_c.f68` array can appear to be missing a registration row when a native note stores `[1]`. The exact ordinary 2026 getter gives both states arrowhead style `1` for the first attachment: an index outside the stored `n70` count returns `1`, while a valid index reads the actual style word.

The [source-bound record](../../../../../../../re/solidworks/records/DrawingPlainNoteRenderOwners2026.md) joins exported `moDisplayItem_c::getArrowHead` to the actual detail owner, the indexed getter and `setArrowHead`'s `su_CUIntArray::SetAtGrow` producer. The values are `arrowHeadStyles`; the attachment-point objects belong to the separate `f58` array. Current version 19000 preserves the stored style words.

Preserve the actual array and count in archival read/write. When diagnosing a renderer failure, compare the actual getter result and attachment owner instead of inventing a registration interpretation or copying `[1]` from a saved document. Equality of this getter alone does not prove equivalence for every other native consumer or qualify missing text pixels.
