# SOLIDWORKS drawing view properties

`open_document(source, strict=False)` and `kit decode SOURCE --partial` read the ordered native SOLIDWORKS 2026 drawing concept through its first resolved list. A single unformatted sheet can have an external part front view. Its native orientation name, scale ratio and model-to-sheet transform are available on the portable view. Definition is checked against the independent sheet, header and reference indexes. The normal JSON writer preserves the resulting properties.

The [SDK view check](../../../../../re/solidworks/measurements/2026/DrawingSdkViewRead01.json) verifies an empty source and two front-view placements against the pinned authoring oracle. Annotations, native styles and geometry display records remain outside this inspection profile. Strict drawing reads and native writes still require qualification. [Release read grammar and verification](../../../../../re/solidworks/records/DrawingSdkInspection2026.md)
