# SDK origin corner rectangle construction

This internal SDK construction slice adds a real native origin coincidence to a fresh dimensioned rectangle. It does not enable public writing or admit an FCStd source. The complete candidate remains subject to the native lifecycle. The source-only process evidence is [SdkRectangleCornerAnchor01.json](../measurements/2026/SdkRectangleCornerAnchor01.json).

Task `B04-SW2026-RECTANGLE-ANCHOR`, owner `configuration_header`, delivery PR #121. Dependencies are the existing SDK `ProfileGraph`, `OriginGraph`, `MakeRectDimsMut`, common part composer and typed Config/Resolved executors. Exit requires the controlled native width, height and leaf-depth edit/save/reopen trial, followed by root-owned full neutral-source admission. No sealed input is needed by this slice.

## Construction boundary

`Archive.Construction.RectangleAnchors.MakeCornerMut.MakeCornerMut(profile, origin)` receives the actual generated profile and the same part's actual origin. It runs after the rectangle's two length dimensions and four horizontal/vertical relations, before the common boss composer. It returns a typed `CornerGraph`; it mutates the actual sketch only after checking every prerequisite.

The admitted scope is format 19000, a fresh ordinary part, canonical Front Plane at zero, four positive ordered rectangle vertices with vertex zero at the origin, four actual local lines, two existing point-distance drivers, four existing axis relations, and no prior origin/coincidence group. The origin is the model's fresh one-point origin profile with an empty creation log. Other frames, centered rectangles, unrelated origins, prior external relations and malformed local slots fail before publication.

The four contour points remain `ProfileGraph.GeometryValue.PointValues`. The external origin point is a fifth row in the native sketch point collection, returned separately in `CornerGraph.PointValues`. It is not an extra contour vertex. The common boss still consumes the original four-edge loop.

## Model-derived fields

| Owner and field | Classification | Rule |
| --- | --- | --- |
| Origin selection feature ID | Derived | Read the actual allocated `moOriginProfileFeature_c.f08` from the same generated model |
| Origin selected local point | Derived | Bind the actual origin sketch and its sole point; local archive slot is zero |
| Origin point mark | Derived | The referenced point's permanent mark is its existing creation ordinal; publishing assigns this mark to its `f08` |
| Selection component | Derived ownership | Clone the actual same-owner self unit component into a separate node, as the native reference constructor does |
| Selected point handles | Derived | Use the actual owning sketch and actual entity order; compact and extended index forms agree before emission |
| Backup point | Derived geometry | Transform the actual origin point through the verified matching profile frame |
| External entity label | Derived text | `Point{origin ordinal}@{actual origin feature name}` |
| External point row and creation ID | Derived | Append one kind-1 point row after the four contour points; assign ordinal five and advance the sketch's next point-creation counter to six |
| Coincidence operands | Derived | Operand one selects the new external point, operand two selects contour vertex zero |
| Entity use counts | Derived | Add one use to the local corner and one to the external point; preserve every existing driver and axis use |
| Persistent feature/dimension allocation | Derived | The inline logical relation consumes no new model ID; dimension IDs 19/20 and terminal allocator 27 remain unchanged in this scoped fresh part |

The origin selection's creation time is **not** its feature FILETIME or document creation date. The source-pinned empty creation-log branch returns the native unset-time value `0x278d00` (`2592000`). This constructor accepts only that fresh empty-log profile. [Creation-time rule](../../../Documentation/Gotchas/Conversion/Solidworks/FeatureReferenceCreationTimes.md)

## Constructor defaults and field grammar

The source evidence is the original licensed `sldmodu.dll` SP05.2 build `34.5.2.0604`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`, AMD64 machine `0x8664`. No module, decompilation listing or captured property row is part of the implementation or evidence receipt.

[Corner constructor evidence](RectangleCornerAnchorConstruction2026.md) binds the native external-entity constructor, component sketch selection constructor, external point insertion/permanence path and binary coincidence constructor. [Disclosed source ownership](RectangleAnchorSources2026.md) supplies independent original/width/height observations. The SDK factory uses those shared rules, not values read from those documents.

| Constructor range | Range SHA-256 |
| --- | --- |
| `0x4c434f70..0x4c434fc5` | `c51b5f04034df943df877391ebe1f5a9d278603f32352c739a8c5b259126ba48` |
| `0x4b7e8750..0x4b7e88a1` | `f9d7f12038c43da25034f2970444fa0752b998b81a2d9312f66f5e1ab49937f4` |
| `0x4c700fb0..0x4c701121` | `3af655fe414951418c6577069c88b34c5db74b30c3e651906aad56206001a216` |
| `0x4c410460..0x4c410570` | `0a03c7cf7147afe9d604c785256b42491b97ed2dff36728ba05e7347440a92c4` |
| Inline binary relation serializer `0x4c58b970..0x4c58c699` | `ea09f6703dd6890985ce8de4b1e70a21393aefebf70919dc6ba7572cefd086e3` |

The external point inherits the existing ordinary point constructor, then takes the native type-6 external-point branch and clears the two transient low flag bits. Its segment adjacency remains empty. The inline relation uses native type 9, two operands, initial logical state `0xfffe`, unassigned persistent identity `-1`, and the source-defined zero/null/negative optional states. Those are constructor states, not a universal assertion about vendor-saved solver state.

The wrapper uses a direct component-sketch selection, no transforms, no parent component link, archive version 19000, negative unset selectors and a backup point computed from geometry. Its fresh last-access stamp `f08` is 101 and its configuration selector `f0c` is −1. Native `iUpdateLastAccess` can replace those with the target header stamp and active configuration ID. The existing `moCompFeature_c` codec owns the common fields. [Wrapper write-state rules](PlanarMateWrapperWriteState2026.md)

The new `AnchorFields` layouts add four concrete schema-one owners and one inline relation helper. Original `CRuntimeClass` metadata independently identifies all four wire schemas as one:

| Concrete class | Descriptor address | Native object bytes | SHA-256 of first 16 descriptor bytes |
| --- | --- | --- | --- |
| `sgExtEnt_c` | `0x4dafc288` | 56 | `0af5d7284994cf150cfc7a9116c99e59bed145bb48f9a08fa6a0e896a3acba82` |
| `moCompSketchEntHandle_c` | `0x4dade2f0` | 280 | `2f295413a81eefec74afae6f3255cf4e558c45ec92262f1c1ab4575936d5cca4` |
| `moSketchExtRef_w` | `0x4daf3610` | 200 | `b0d2eaf92d3391b028492d2666293f7a6bad82b392acf4d9f015960a98afb52e` |
| `moPointBackedUpData_c` | `0x4daf2950` | 32 | `58a70f812413627e4b4b3b44d6843c30fc5d3101c7d537de5c867ce7a77f23eb` |

`moRefWrapper_c` is a shared field-layout helper, not a new standalone schema registration. Its original descriptor is at `0x4daf2ef0`, object size 176, descriptor-prefix SHA-256 `9c7ab2e4fd2158e38d248f70e5ea2ff8460e3fca4f92ca786dd1c2632bc436fb`. The point wrapper admits the concrete component-sketch selection branch. Other selection types and alternate archive conditions remain unqualified. The shared body executor still rejects every version other than 19000.

## Executable evidence

Three independently authored neutral requests cover `31.75×18.125×9.625 mm`, `14.375×27.625×6.875 mm` and `20×30×10 mm`. Each runs two deterministic guarded builds, fresh typed preparation and an independent mathematical research construction in separate processes. All ten logical streams must equal that independently generated counterpart. No saved native input participates in any generated candidate.

Each build also rejects fourteen malformed scopes without publishing partial anchor mutations. Rejections include a foreign origin, moved origin, nonempty creation log, wrong local handle slot, wrong line endpoint slot, stale entity use count, wrong point-creation counter, another coincidence and a second anchor application.

The two disclosed native-saved skew/step controls exercise complete SDK Config/Resolved read→write byte identity. The original corner check seeded the Resolved map with the research-read Config after the SDK stopped at a missing ghost-body record. The [populated ghost-body continuation](SdkGhostBodyConfig2026.md) now checks the three disclosed corner original and edited controls through the SDK alone. Both complete streams and their maps are exact in all three files. The [historical cache boundary](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Resolved/NativeAnchorConfigCachePrecedesResolved.md) retains the earlier separate outcomes.

`ReplaySdkCorner.py --root ROOT --output NEW_DIRECTORY` repeats the source-only three-design process proof. `PrepareSdkCornerOracle.py` binds the generated f14a-sized synthetic candidate, its request/build/prepare/counterpart records, writer closure and pristine L1 control. `InspectSdkCorner.py verify PACKET --packet-sha256 SHA` verifies that frozen deck without starting SOLIDWORKS. Root alone can run its eight fresh native phases.

## Native and source-admission boundary

The new native packet edits width, height and leaf depth independently from the identical immutable original. Each edit saves separately and reopens in its own new process between healthy pristine controls. It measures every contour corner against `(0,0),(length,0),(length,width),(0,width)`, all three driving parameters, seven actual relation owners, full constraint after rebuild, the complete neutral-predicted feature tree, one solid, analytic volume/area/mass/centroid and unchanged input bytes. Its model-origin selection uses the already disclosed COM selection path and records actual object equality for the coincidence entities.

The first SDK native packet opens the generated shape in all three candidate processes with zero load warnings and errors. Both bracketing controls pass. The observer stops before edits at its origin-point identity predicate. The exact raw failure is SHA-256 `4fa47be9efb275bf5e8be234ca0213f20458a1ce2fdb7b3fc5627a774dc33547`. A matched native read-only probe passes for both the original vendor-authored corner and the unchanged SDK candidate, with both controls healthy. The external sketch point and its target model-origin point retain distinct COM identities. The probe result SHA-256 is `6e822733fe51dfb0aca6dfb91b5ec70500dff7c06a808fe2fc4d93c2c7411995`. The independent edit lifecycle remains a separate gate.

The f14a-sized request is synthetic. Exact original FCStd support/placement, source member retention, provenance, properties, visibility, material identity and public neutral admission remain root-owned work. F14c's authored XZ support/orientation is outside this canonical Front-Plane constructor. No held-out source, native payload or observation is opened by this work.

At this constructor freeze, the public typed line reader excludes kind-1 external points and its rectangle-dimension reader excludes a nonempty `log_g2` array. An owner-aware public origin-coincidence projection is a separate required slice. The constructor and native packet do not silently widen those reader predicates.
