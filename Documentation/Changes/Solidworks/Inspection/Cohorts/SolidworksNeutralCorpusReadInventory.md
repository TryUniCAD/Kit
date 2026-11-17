# SOLIDWORKS neutral corpus read inventory

[MeasureNeutralCorpus.py](../../../../../re/tooling/sw2026/MeasureNeutralCorpus.py) measures the SDK's available FreeCAD inputs before SOLIDWORKS generation. Supply a private source inventory JSON, a fresh output file path and the exact `--inventory-sha256`. Each inventory row lists one file identity by SHA-256, size and candidate paths and supplies its declared FreeCAD object types. The instrument verifies the source bytes and uses the public strict SDK reader with B-rep and tessellation disabled.

The published result contains aggregate timeline, declared type and sketch relation counts. All 162 input identities read successfully, two contain assembly graphs, and 132 contain at least one native feature definition. The earlier path-based pass produced the same counts and resolved one external link that the byte-input pass reported as unresolved. [Receipt](../../../../../re/solidworks/measurements/2026/NeutralCorpusRead01.json) [Input mode gotcha](../../../../Gotchas/Conversion/Freecad/ByteInputsLackExternalReferenceOrigin.md)

This inventory measures read coverage for the available sources. The original 165-part and five-assembly benchmark membership and the generated-output audit remain open.
