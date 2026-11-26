# Verify exact SOLIDWORKS sketch intent natively

The two exact native archives from the [SI sketch replay](../Encoder/SolidworksExactSketchIntent.md) opened and rebuilt in separate SOLIDWORKS 2026 SP04.1 `34.4.1.1011` processes. The application returned the same ordered XY binary64 words as the corresponding independently authored references. All four or five consecutive endpoints shared the expected API point identities. Z remained positive zero. The measured sketch frame, D1, millimetre unit enumeration and solid geometry matched. [Exact measured proof](../../../../re/solidworks/records/VendorBlindBossNativeSketchProof.json)

| Profile | Native D1 in metres | Solid faces, edges, vertices | Volume mm³ |
| --- | --- | --- | ---: |
| Baseline | `0x1.d4e8fb00bcbe6p-7` | 6, 12, 8 | 7,584.3 |
| Separate five-line reference | `0x1.625204af92296p-7` | 7, 15, 10 | 12,343.0395 |

A private baseline copy completed an unchanged SaveAs, followed by a fresh read-only reopen and rebuild. The exact XY values, endpoint aliases and D1 persisted. All eight positively owned lifetimes exited normally in 92.701 seconds. The stock controls passed before and after the batch. [Phase timings and private retrieval](../../../../re/solidworks/records/VendorBlindBossExactSketch.md#verified-native-sketch)

The full native unit-format arrays differ despite the common millimetre length unit. Configuration and display-state names, annotation views and document-wide plane visibility also differ. This evidence covers both exact research candidates and the baseline lifecycle. The five-line source is a separately authored matching reference. Held-out generalization, complete ordinary source preservation and public SDK qualification remain open. [Unit formatting observation](../../../Gotchas/Conversion/Solidworks/Archive/Presentation/LengthUnitAndDisplayPrecisionAreSeparate.md)
