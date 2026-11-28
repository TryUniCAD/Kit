# Internal linked Front Definition codec

The internal SDK can write and completely read the Definition stream for one ordinary linked Front drawing view. The public adapter remains read-only. The neutral semantic factory and surrounding metadata constructors remain separate work.

Use `FrontGraph`, `WriteFrontDef` and `ReadFrontDef` under `convert.adapters.solidworks.Drawing.Definition.Linked`. Supply the complete typed UI drawing owner and explicit archive version 19000. The writer returns bytes, a computed object map and grammar evidence. The reader consumes the entire stream and returns the corresponding typed graph and map.

The admitted graph has one active unformatted ANSI A landscape sheet and one `*Front` model view at explicit 1:1 view scale. Preserve actual sheet, support, internal-reference, property-manager and external-directory aliases. The two model references must share the same child entry and configuration. The external feature must point back to the internal reference and the containing drawing file. Its name uses a pooled handle.

Names, sheet scale, units, provenance, view position and child dimensions come from the supplied graph. Other view orientations, nonunit view scale, annotations, preview maps, populated display state, alternate reference modes and optional caches raise. Abort file construction after any codec error. The existing blank profile continues to reject populated views.

Feature runtime owners are reconstructed from serialized containment during complete readback. They are not extra wire fields. Header objects and body objects continue to use one Definition map. See the [ownership gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingRuntimeOwnersFollowContainment.md).

Four independent new designs each pass two fresh processes, including long Unicode text and different child dimensions and placements. All complete Definition bytes, final maps and surrounding logical streams match independent generation. Full SDK read/write, independent readback and public drawing projection preserve actual child identity. Twenty-two additional jobs reject the excluded profiles. All thirty processes retain zero runtime input-file access.

These are offline codec checks. This slice does not enable public export, provide complete SDK-only drawing construction or add native acceptance. See the [field/source ledger](../../../../re/solidworks/records/DrawingLinkedDefinition2026.md), [process receipt](../../../../re/solidworks/measurements/2026/SdkDrawingFrontDefinition01.json) and [blank Definition boundary](DrawingDefinitionWriting.md).
