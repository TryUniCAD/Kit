# SDK linked Front drawing Definition codec

The internal SDK now emits and completely reads the version-19000 Definition graph for one ordinary externally linked `*Front` view at explicit 1:1 view scale. Four new neutral requests reproduce independent complete stream bytes, native object maps, all surrounding logical streams and real linked-child identities. This is an internal codec boundary. Its semantic factory remains in research, the public adapter stays read-only, and this tranche adds no native acceptance measurement.

Task: **B04-SW2026-DRAWPROPS / SDK linked Definition**. Owner: `/root/configuration_header`. Delivery: PR #121, with root owning Git and the Windows oracle. Dependencies are the [complete blank codec](DrawingDefinitionWriter2026.md), shared header/resolved executors and previously proved drawing/view construction. The exit condition for this slice is a complete typed one-view stream, exact independent readback, strict profile rejection and no runtime input-file access. Complete SDK-only neutral drawing construction and the full CAD criteria remain open.

## Construction and source authority

The new [Linked modules](../../../src/convert/adapters/solidworks/Drawing/Definition/Linked/) add view field layouts, support/reference owners and a separate admission profile. They reuse the unchanged `WriteDrawMut`, `ReadDrawMut`, sheet field writer, canonical header codec and full blank/UI layouts. They do not weaken the existing blank guards. Root's shared UI-field relocation retains those API and byte boundaries.

All model addresses below refer to the pinned `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Other module identities remain recorded in the linked findings. This tranche reuses retained source facts. It reads no vendor binary, saved source document, prior native trial output or hidden input.

| Owner or boundary | Classification and wire rule | Source and confidence |
| --- | --- | --- |
| Drawing framing, model, inline header, UI tail and trailer | Existing typed fields and actual graph owners; lengths/tags/maps computed by shared executors | **Confirmed** retained [Definition grammar](DrawingDefinitionGrammar2026.md) and [blank codec](DrawingDefinitionWriter2026.md) |
| `moDrView.Archive` | Embedded display array, inherited model feature, explicit frames, scalar bounds/state, presence-governed owners and counted maps, in native field order | **Confirmed** retained serializer `0x4c958dc0`, [absolute view fields](DrawingAbsoluteViewFields2026.md), shared [research grammar](../../tooling/sw2026/serial/defs/Drawing.py) |
| View context | Set `0x40` for the affected common body only if absent, restore the enclosing bit before the outer suffix | **Confirmed** `0x4c958f87` and `0x4c95cb24`; [context gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingViewsSetArchiveContext.md) |
| `moAbsoluteView` suffix | Inherited view, absolute selector, authored orientation name and typed current-version state fields | **Confirmed** named constructor `0x4b744590` and the retained [field table](DrawingAbsoluteViewFields2026.md) |
| Sheet and active view | The actual root `f1430` is the owned sheet. Its fourth child is the one view; the first three sheet supports retain their real aliases | **Confirmed** [sheet/view ownership](DrawingDefinitionGrammar2026.md#sheet-and-view-ownership) |
| View supports | Ordered detail folder, sheet plane/profile, model plane/profile. Actual `f630/f7c8/fde0`, plane-wrapper `ff8` and component owners must agree | **Confirmed** `createProfileFeature` at `0x4c9952b0`, [construction](DrawingFrontViewConstruction2026.md), [support roles](DrawingScaledSupports2026.md) |
| Internal and property references | Shared `moReference_c` wire layout with distinct concrete runtime classes; both reference the actual one-entry external directory and same child configuration | **Confirmed** [link construction](DrawingFrontViewConstruction2026.md#object-graph) and shared [occurrence grammar](OrdinaryOccurrenceConstruction2026.md) |
| External feature | Shared interface fields, live internal-reference backlink and nonpattern suffix. Drawing file kind is 4, the child directory kind is 2, name is a pooled handle | **Confirmed** current wire rule at `0x4c179410` and `0x4c178a30`, [wire proof](ExternalReferenceWire2026.md), ordinary drawing construction; broader filtered contexts remain unqualified |
| Property array | An allocated, empty concrete `suObArray`; count follows its actual empty rows | **Confirmed** bounded empty-array use in retained drawing ownership. [2026 map](../../data/Serialization/SerializeMap2026.json) binds `suObArray::Serialize` to `sldmfcu!0x3c8cd950` through the model import. Populated property arrays remain outside admission |
| Geometry/presentation values | Supplied typed model fields; this codec adds no captured defaults or geometry derivation table | Existing [projection](DrawingFrontViewConstruction2026.md#projection-values), [view state](DrawingAbsoluteViewFields2026.md) and [model constructors](ModelConstruction2026.md) |
| Feature runtime owners after read | Reconstruct from actual serialized child lists, the view's internal reference and component-property manager. No additional owner word is emitted | **Confirmed** field-layout absence and complete generated read/re-emission; [runtime-owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingRuntimeOwnersFollowContainment.md) |

The external-feature profile does not reuse the assembly-specific guard. That guard requires file kind 3 and ordinary assembly ancestry. The drawing boundary instead verifies kind 4, actual containing-drawing file handles, the pooled name, refreshed persistent ID, absent configuration selector and reciprocal internal-reference backlink. Direct CString mode, older releases, patterned references and special filter conditions stay unqualified. Research registry provisional labels are not changed by this codec.

## API and admission

`FrontGraph` carries the complete `uiDrawingDoc_c` owner and explicit archive version. `WriteFrontDef` validates it, walks every concrete class through the bounded schema map, reuses the existing empty/annotation guards and writes a new Definition map from 1. `ReadFrontDef` consumes the complete stream, reconstructs nonpersisted containment owners and validates the same graph. It returns `FrontRead` with the graph, actual final map and usage evidence.

Admission requires archive 19000, schema-one owners, one active unformatted ANSI A landscape sheet, one unrotated unit-scale `*Front` model view, the ordered support pairs, one actual child entry and an empty property array. Names, units, sheet scale, provenance, positions and child geometry come from supplied owners. Other orientations, nonunit view scales, additional views, alternate reference-name modes, preview/detail maps, annotations, populated display lists and sketch caches fail explicitly. Complete readback also rejects trailing bytes and unsupported versions.

No recorded span, field operation, saved row, payload fallback or vendor-runtime dependency is added. The production modules import no research code. Complete surrounding metadata and semantic graph construction remain separate dependencies.

## Executable proof

[DrawingFrontDefinitionProcess.py](../../tooling/sw2026/DrawingFrontDefinitionProcess.py) constructs canonical and independent linked bundles from the same newly authored neutral request. Only the independent live graph is projected into canonical SDK owner representations. The worker requires complete Definition byte identity and map identity, full SDK read/write identity, a separate complete research read, unchanged surrounding logical streams, public drawing readback and the actual child configuration/path. Both blank read and blank write must still reject the populated stream.

| Fresh request | Child width/height/depth, metres | Definition bytes | Map index | Variation |
| --- | --- | ---: | ---: | --- |
| `LinkedAlpha` | 0.0317 / 0.0263 / 0.0149 | 28,870 | 172 | Independent names, identity and 11:3 sheet scale |
| `LinkedBeta` | 0.0431 / 0.0187 / 0.0093 | 29,560 | 172 | Long Unicode view name |
| `LinkedGamma` | 0.0239 / 0.0341 / 0.0173 | 28,870 | 172 | Independent shifted view position |
| `LinkedDelta` | 0.0373 / 0.0211 / 0.0127 | 28,870 | 172 | A second distinct shifted position |

Each positive runs twice with identical stdout. Twenty-two additional complete jobs reject unsupported versions, orientation/scale/rotation, wrong active-sheet/view ownership, broken directory/property/configuration links, external backlink/name/file modes, support aliases/components, annotations, view caches, preview state, UI profile, concrete schema, duplicate views and reader tails. All thirty fresh processes pass their expected outcome with zero runtime input-file access.

The final 26-code/test-file manifest SHA-256 is `737893693df711780688fe3d547cc84ce7608435a00eceef82c36660540e0d44`. The private final process proof SHA-256 is `d7c693bab704e6736e36906506e38608124320fd5a854a27c27f4fccd8ae03c0`. Source hashes are checked before and after the cohort. The earlier successful cohort is retained privately; the final freeze groups two equivalent integration assertions to satisfy the declaration-size rule, without changing production or worker bytes. The [sanitized receipt](../measurements/2026/SdkDrawingFrontDefinition01.json) records exact source, neutral input and generated artifact hashes.

The focused integration functions `TestFrontDefs` and `TestFrontGuards` live under `tests/Convert/Solidworks/Research/Drawing/Linked/`. A private replay runner checks the frozen owned files and requests, then repeats all thirty processes from a separately supplied checkout. This allows root to verify shared-field integration against the same byte and semantic observations.

Steering, Black, Mypy and Pyright pass for all 25 production/test modules. The observed donor scan is clean across 3,670 files. Three existing unrecognized Pyright configuration messages remain visible. This offline proof establishes the complete bounded codec; it adds no native save/reopen measurement or held-out acceptance and enables no public writer.
