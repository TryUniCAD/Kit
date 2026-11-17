# SOLIDWORKS drawing layout inspection

Use `open_document(path, strict=False)` or `kit decode SOURCE --partial` to inspect an ordinary SOLIDWORKS 2026 drawing. The adapter recognises `solidworks.slddrw` and returns its sheet name, dimensions and scale in `CadDocument.drawing`. For one external part view it also returns its sheet position, paper outline, saved model path and selected model configuration. The document uses metres and the normal interchange JSON writer preserves its drawing records.

The initial profile covered a single unformatted sheet with zero or one model view. It reported unqualified view properties, annotations, styles and rendered geometry through `slddrw.layout_inspection`. The [view-properties follow-up](SolidworksDrawingViewProperties.md) adds the typed Definition view information. Strict reads and native drawing writes require further qualification.

The [SDK layout process](../../../../../re/tooling/sw2026/serial/CheckSdkDrawingLayout.py) verifies the three disclosed native sources against the authoring oracle. It exercises public read and JSON write, checks the native header's layout and references, and verifies that strict reads and unsupported writers reject a drawing. [Drawing inspection evidence](../../../../../re/solidworks/records/DrawingSdkInspection2026.md)
