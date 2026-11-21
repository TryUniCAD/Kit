# Internal SOLIDWORKS drawing sheet writer

`convert.adapters.solidworks.Drawing.Definition.Writing.WriteSheetMut.WriteSheetMut` writes the complete current-version own-field body of a typed `moDrSheet` node. The public SOLIDWORKS adapter remains read-only. This function is an internal archive codec, not a complete drawing export API.

Pass the active SDK `BodyWriter` and actual `ArchiveNode` after the inherited `moModelFeature_c` body has been serialized. The writer must retain the same archive map, concrete child object writer and geometry layouts. The function emits fields from the supplied graph using the shared `NativeField` executor. It preserves object identity and derives collection counts from modeled rows; it reads no files and creates no saved-data fallback.

The admitted boundary is archive version 19000, `moDrSheet` schema one and zero archive-condition flags. Native presence flags must be explicit. Unknown annotation state, nonempty ink views, alternate schemas/releases and specialized filters raise before this own body changes the buffer or map. Other malformed values use the shared field executor's diagnostics; callers must abort the enclosing stream on any error.

The caller owns semantic sheet construction, inherited fields, persistent IDs, complete object graphs and the remaining Definition payload. Do not invoke this body as a standalone document or start a new map for already serialized children. No public writer registration or general drawing capability is added.

The focused process coverage constructs two independent blanks and two front-linked rectangular parts, runs each in two isolated interpreters, compares every generated logical stream with the existing serializer and reads the resulting container through the public drawing API. Unicode text changes increase the sheet body from 192 to 796 bytes. Seven unsupported complete jobs reject without successful output. The runtime input-read guard records zero attempted reads.

These are offline component checks. They do not establish new vendor acceptance or complete CAD support. See the [source and field ledger](../../../../re/solidworks/records/DrawingSheetWriter2026.md), [process receipt](../../../../re/solidworks/measurements/2026/SdkDrawingSheetWrite01.json) and [archive-context gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingSheetFieldsNeedTheirArchiveContext.md).
