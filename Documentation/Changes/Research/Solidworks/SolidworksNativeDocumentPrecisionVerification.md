# Verify SOLIDWORKS boss document precision natively

The exact four-place and two-place combined blind-boss files from the [unit precision replay](../Encoder/SolidworksBossDocumentUnitPrecision.md) opened and rebuilt read-only in fresh SOLIDWORKS 2026 SP04.1 `34.4.1.1011` processes. The document-length display record and the independent document linear-precision getter agreed on four and two places respectively. [Exact measured proof](../../../../re/solidworks/records/VendorBlindBossNativeUnitPrecisionProof.json)

| Observation | Native reference | Generated four-place | Generated two-place |
| --- | --- | --- | --- |
| Complete `GetUnits` result | `[0, 1, 8, 2, 0]` | `[0, 1, 1, 4, 0]` | `[0, 1, 1, 2, 0]` |
| Linear, angular, mass, force, energy, power, time decimal places | 2 | 4 | 2 |
| Dual linear decimal places | 2 | 2 | 2 |

Across 24 recorded native document unit preferences, the two-place file and stock differed only in the stored fraction denominator. The observed decimal millimetre display does not use this denominator. The generated pair kept exact SI coordinates, endpoint aliases, linked D1, active configuration, hidden Top, the two global plane getters and the same measured one-solid topology. Bounds and pre-rebuild measures matched. One-ULP differences in volume, mass and centre-of-mass X after rebuild remain within the existing measured geometry checks. [SOLIDWORKS GetUnits documentation](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDoc2~GetUnits.html?format=P&value=)

The native lifecycle took 55.642 seconds across four normal read-only lifetimes. Independent stock controls were healthy. No source or candidate was changed. The evidence covers native open and rebuild of the two exact generated choices. A length-only setter, save and reopen of the two-place file, and full source unit-state preservation remain separate requirements. [Timings and private retrieval](../../../../re/solidworks/records/VendorBlindBossExactSketchPresentation.md#verified-native-unit-precision)
