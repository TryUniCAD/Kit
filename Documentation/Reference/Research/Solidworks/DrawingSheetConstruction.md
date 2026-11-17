# Internal fresh drawing sheet construction

Use `MakeBlankSheet` under `convert.adapters.solidworks.Drawing.Construction.Sheet` to build a complete blank-sheet/support graph from neutral inputs. The public SOLIDWORKS adapter remains read-only.

Supply `SheetBuild` with paper and scale inputs, a sheet/property-view name, three support names, document length unit, the caller-reserved first persistent ID, creation time and exact target provenance. Also supply the actual drawing owner and an ordinary self component with that owner. Reserve four consecutive IDs in the document allocator before calling this constructor.

The result contains the sheet, absolute support plane, empty profile sketch, detail folder, separate UI sketch and next persistent ID. Attach those actual objects when composing the parent drawing. The constructor does not replace existing sheets or update parent metadata.

The admitted profile is one fresh unformatted ANSI A landscape sheet at archive version 19000, SP05.2. It computes paper dimensions, metric or imperial zones, native scale frames and profile FILETIME from the supplied intent. It keeps the plane handle unregistered until the inline reference exists and constructs an exclusive unit-component copy. Unsupported paper, target, scale, text, owner or provenance input raises before allocation.

The complete Definition codec can serialize this graph through its actual parent. Four independently authored requests match complete Definition and container logical streams after SDK construction. Eight positive fresh processes and fourteen rejection processes pass, with full SDK read/write, public readback and zero runtime input-file access. These are offline component checks.

The parent model/style and metadata factories remain in research. Complete SDK-only drawing export, broader sheet/view/annotation construction and native qualification remain open. See the [source ledger](../../../../re/solidworks/records/DrawingSheetConstruction2026.md), [process evidence](../../../../re/solidworks/measurements/2026/SdkDrawingSheetConstruction01.json), [Definition codec](DrawingDefinitionWriting.md) and [scale arithmetic gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingScaleReciprocalsKeepNativeOrder.md).
