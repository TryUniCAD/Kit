# Typed linked Front drawing Definition codec

The internal SDK now writes and completely reads the Definition stream for one ordinary externally linked Front view. It reuses shared model/header executors and the existing sheet/UI layouts. Object tags, lengths, counts and map indexes follow actual typed owners. The linked view, active sheet, support pairs and both child references retain their real aliases.

Use `FrontGraph`, `WriteFrontDef` and `ReadFrontDef` under `Drawing.Definition.Linked`. Admission is limited to archive version 19000, one unformatted ANSI A landscape sheet, one unrotated `*Front` view at explicit 1:1 scale, empty annotations/display caches and the ordinary one-child reference profile. Unsupported graphs fail explicitly. The blank codec remains unchanged, the semantic factory stays in research, and public writing stays disabled.

Four fresh neutral designs each pass two isolated processes with complete stream/map identity, SDK read/write, independent readback, all surrounding logical streams and public drawing projection. Twenty-two further jobs reject excluded ownership, mode and payload cases. All thirty processes pass with zero runtime input-file access. Steering, Black, Mypy, Pyright and the donor scan pass. This tranche performs no Windows run and claims no new vendor or held-out acceptance.

See the [usage guide](../../../../../Reference/Research/Solidworks/DrawingLinkedDefinition.md), [source ledger](../../../../../../re/solidworks/records/DrawingLinkedDefinition2026.md), [process receipt](../../../../../../re/solidworks/measurements/2026/SdkDrawingFrontDefinition01.json) and [runtime-owner gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingRuntimeOwnersFollowContainment.md).
