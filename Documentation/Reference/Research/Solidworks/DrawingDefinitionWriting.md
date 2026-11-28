# Internal blank drawing Definition codec

The internal SDK can serialize and read a complete version-19000 blank drawing `Contents/Definition` stream. Public SOLIDWORKS writing remains disabled. The semantic drawing factory remains in research.

Construct a `BlankGraph` from a complete typed `uiDrawingDoc_c` owner and an explicit archive version. Call `WriteBlankDef` to obtain the stream bytes, computed archive map and usage report. Call `ReadBlankDef` for a complete typed readback. These functions live under `convert.adapters.solidworks.Drawing.Definition.Emission`.

The input graph must use canonical SDK header objects and the shared body field mappings. Header object collections use ordered tuples of actual nodes. Embedded body collections use ordered row mappings. Preserve the actual sheet, support, property-manager, layer-manager and header aliases. The codec computes tags, collection counts and map indexes from those owners.

The supported graph has one unformatted ANSI A landscape sheet, no drawing views or annotations, an empty sketch and empty layer/block/model-link collections. It requires schema-one drawing owners and archive version 19000. Names, positive scale values, property text, provenance, units and modeled style settings come from the graph. Unsupported owners or optional payloads raise. Abort the enclosing file construction on any codec error.

The complete stream reuses the shared model layouts, existing header codec and unchanged sheet own-field writer. It emits the model header inline with normal object tags in the active Definition map. It also writes the UI state and drawing trailer. It reads no file or saved payload and has no CAD runtime dependency.

Four independent neutral requests each pass two isolated process runs. The requests vary scale, provenance, independent block identities, long Unicode text, imperial units and drafting vocabulary. Every complete Definition and surrounding logical stream matches independent generation. The full SDK read/write round trip and independent reader consume the entire stream and preserve the native map. Twelve unsupported complete jobs reject without output. These are offline codec checks, with zero runtime input-file access.

This boundary does not provide a neutral-document export API or qualify populated views, sheet formats, annotations, other paper profiles or new native save/reopen behavior. See the [source ledger](../../../../re/solidworks/records/DrawingDefinitionWriter2026.md), [process receipt](../../../../re/solidworks/measurements/2026/SdkDrawingDefinition01.json), [sheet writer](DrawingSheetWriting.md) and [inline-header gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingInlineHeadersNeedTheDefinitionMap.md).
