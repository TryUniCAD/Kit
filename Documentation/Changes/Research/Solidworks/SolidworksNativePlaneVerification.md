# Verify generated SOLIDWORKS construction-plane visibility

Two exact files from the [plane research writer](SolidworksDocumentPlaneIntent.md) opened and rebuilt in separate SOLIDWORKS 2026 SP04.1 `34.4.1.1011` processes. The Off file returned `false` through both document-level getters. The On file returned `true` through both getters. The two native observations agree on every other captured field, including the individual plane visibility flags, feature tree, sketch, dimensions, and solid.

The writable On copy accepted a D1 edit from 14.31 to 19.87 mm. After rebuild, save and a fresh read-only reopen, both document getters remained `true`. The edited solid retained 6 faces, 12 edges and 8 vertices. Volume went from 7,584.3 to 10,531.1 mm³. Its saved Definition low word retained bit 17 and the D1 driver retained the exact edited SI word. The immutable inputs were rehashed after the run. [Exact proof and phase timings](../../../../re/solidworks/PlaneVisibility/NativeCandidateProof.json)

| Fresh process | Active seconds |
| --- | ---: |
| Stock control before | 12.650 |
| Independent edited reference | 11.389 |
| Generated Off | 11.719 |
| Generated On | 10.834 |
| On edit and save | 13.836 |
| Saved On reopen | 13.120 |
| Stock control after | 12.173 |

Seven lifetimes took 87.994 seconds from first start to last exit. All reported zero open or save errors and warnings and exited normally. Both stock controls agreed exactly. The generated inputs start with `0x1.d4e8fb00bcbe7p-7` metres for the scoped literal-millimetre geometry. The independent stock source uses `0x1.d4e8fb00bcbe6p-7`. The edit saved and reopened as `0x1.458cd20afa2f0p-6`. One-ULP rebuild changes in mass, volume and centre-of-mass X use the existing bounded native measurement comparisons. [Native mass readback gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Presentation/NoOpSaveCanShiftMassReadbackOneUlp.md)

This qualification covers the two generated archives on the measured build and the On edit derivative. A separate held-out geometry, alternate display overrides, ordinary vendor-source admission and public SDK publication remain open. Retrieve the private records and exact helper copies only through the [native replay guide](../../../../re/solidworks/PlaneVisibility/FieldAndWriter.md#verified-native-pair).
