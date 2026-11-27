# SOLIDWORKS boss document unit precision

The [offline unit precision command](../../../../re/solidworks/records/VendorBlindBossExactSketchPresentation.md#compare-document-unit-precision) uses the existing combined blind-boss request and accepts an explicit precision of two or four. It applies the value through the typed document-unit recipe. The ordinary combined command still generates the original four-decimal archive.

Two fresh precision-two replays produced the same archive. The only clear-byte differences from the default were the first bytes of sixteen typed `f0c` words in Config-0. The independent analysis table, linked SI D1, exact line coordinates, Top annotation, plane visibility word and solid readback agreed. Precision 17 was rejected before output. [Recorded comparison](../../../../re/solidworks/measurements/2026/VendorBlindBossUnitPrecision.json)

Author04 independently stores two-place precision in the same sixteen rows. Its length formatting, density field and absent analysis table still differ. The precision-two archive has only offline SDK and wire verification. [Generated and native precision scopes](../../../Gotchas/Research/Writers/SolidworksDocumentPrecisionChangesEveryUnitRow.md)
