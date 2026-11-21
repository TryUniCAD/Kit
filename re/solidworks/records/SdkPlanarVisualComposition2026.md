# Planar assembly display stores and the part self appearance

Workstream `B04-SW2026-MATES-PLANAR/source-root-projection`, owner `assembly_frontier`, delivery PR #121. The exact prior base is `6992314aee87ce890cdb6e46436521ad081c25cf`. This host proof covers a private neutral-construction choice for two or three direct occurrences, one all-visible parent state and an optional constructor-appearance state for the dimensioned rectangular child. Whole-source writing remains blocked by the saved child renderer and source feature chronology. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Writer model](../../Playbook/WriterModel.md) · [Earlier root and identity evidence](SdkPlanarAssemblyIdentity2026.md) · [Measured composition](../measurements/2026/SdkPlanarVisualComposition01.json)

## Parent compound ownership

Both 2026 SP05.2 parent streams replay exactly without opaque or provisional operations. The selected configuration 0 owns binary state key 1 and XML state `Display State-1`. The XML orders occurrences directly. The standalone store reverses the actual configuration member order and resolves each selection by its live reference ID and name. The context word is `(101 + reference.f3f0) & 0xffffffff`, which evaluates to 203 in both prior sources and their guarded reconstructions.

Each compound row owns a detached `moContextChainComponent_c`, a `moReferenceChain_c` with `f24=1`, one `moExtFeatureList_c`, the single `moExtFeature_c`, its occurrence-name handle and a detached `moExtObject_c`. The live occurrence's separate external feature backlink still points to that occurrence. The detached target drops the backlink according to the standalone context profile. The two self-locator text handles are shared across the rows. The ordinary visible occurrence words are `(1,6,0,1)`, the plane words are `(0,6,1,0)`, and the one component display attribute has internal alias `<Default>_Display State 1`. [Scope and actual owners](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Displays/CheckPlanarView.py) · [Detached constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Displays/MakeVisContexts.py) · [Source maps](../measurements/2026/SdkPlanarVisualComposition01.json)

| Pair | Detached occurrence IDs in wire order | Native store, bytes / terminal map | Generated store, bytes / terminal map |
| --- | --- | ---: | ---: |
| A20 coincident and distance | 25, 24 | 1,247 / 38 | 1,375 / 38 |
| A21 parallel and distance | 26, 25, 24 | 1,439 / 44 | 1,563 / 44 |

The extra native row contributes 192 bytes and six slots. Its objects occupy slots 29–34 in both the disclosed and generated A21 stores. The generated parents share the same ordered occurrences, stamps and ordered mate IDs as their disclosed counterparts. Their store lengths reflect explicit external self locators of 64 and 62 UTF-16 codepoints. Those locators account for the respective 128- and 124-byte extensions. The original header paths are empty. The generated stores' three datum keys join the independently allocated actual datum IDs 14, 13 and 12. The originals use 5, 4 and 3 for the same roles and carry nonempty creation logs. [Prior compound and creation-log rule](ConcentricVisualStateStore2026.md) · [Exact feature ID and clock mappings](../measurements/2026/SdkPlanarVisualComposition01.json)

## Actual child appearance owners

The two saved child stores both replay all 1,789 bytes at terminal map 26. Slot 4 is a schema-one `moCompHolder_c`. Its inherited component reference points to a detached nonexternal unit at slot 6. Slot 8 is the sibling `visStateVisualPropertiesAttribute_c`. Its `f10` owns a separate `moVisualProperties_c` at slot 10. The holder, sketch and origin share the shown state at slot 12. Sketch, origin and three planes each own their own detached unit, and the five features share the separate null appearance attribute. Feature time keys match both header creation logs.

| Observed child owner | A20 | A21 |
| --- | --- | --- |
| Configuration and model RealView ID | `[9,0]` | `[10,0]` |
| Detached holder RealView ID | `[3,0]` | `[3,0]` |
| Definition presence, next ID and object count | `1, [10,0], 0` | `1, [11,0], 0` |

The saved configuration and model appearances agree in every typed field within each part. Their holders differ at RealView ID and asset spelling only. The holder uses `<SystemTexture>\graphics\materials\color.p2m`. The model and configuration use the installed Windows short path to the same stock asset. All three owners in both children contain RealView `f20.f90` and the 70-field DSPBR `f88`. RealView `f74` is float32 0.6 and DSPBR `f2c` is float32 0.2. The exact ordinary reader refuses both Definitions with `SOLIDWORKS part Definition has an alternate renderer profile`. Their complete typed Definition replays still succeed. The public whole-source assembly still refuses with `assembly root contains unprojected model content`. [Child default allocation and asset ownership](ConcentricChildAppearance2026.md) · [Independent roughness semantics](ConcentricStockChildAppearanceCodec2026.md) · [Saved default owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Metadata/EmptyAppearanceManagerKeepsItsAllocator.md)

The independently modeled constructor choice has no assigned renderer resource. It installs a separate selected configuration appearance where the initial config owner is absent, following the previously measured initial-update rule. The child self attribute then owns a third constructor appearance. The shared typed writer emits the same six ordered self, sketch, origin and plane rows at terminal map 26, with 1,166 bytes and actual child feature IDs 18, 17, 16, 15 and 14. Their generated headers use the measured empty-creation-log sentinel. The guarded proof verifies these role and state aliases, the real driver handles, both authored XYZ labels and centreline behavior, and the independent linked Config-0 and ResolvedFeatures round trips. [Initial appearance constructor](VisualConstruction2026.md) · [Child display composition](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Displays/MakePartVis.py)

## Composition proof and scope

The linked pair calls the real `MakePlanarGroup` and `EmitAsmStreams` with explicit neutral presentation. Both display stores for the parent come from the emitter. Its XML agrees exactly with the independent typed XML implementation. Turning on parent visibility changes just COMPINSTANCETREE and VisualStates. Adding the constructor-only child state changes just the child's CMgr and VisualStates and preserves the complete generated parent. Both no-intent builds match the frozen base at the same locator and event.

Twelve guarded writer successes and two strict source read processes are independent. A third neutral design uses a different rectangle, applied dimensions, rigid placements, physical file and nonmonotonic occurrence names. Its reversed compound order follows its actual allocated identities. Ten malformed requests refuse under the guard, including ordering, duplicate visibility, mixed single state, detached stamp, foreign mate, absent or unowned child store, foreign renderer marker and crossed feature clocks. The existing radial proof still reproduces the exact previously native-tested pair and no-intent baseline with 13 refusals. The new planar runs have zero native launches, zero writer runtime input reads and zero new held-out or public-writing qualification.

The current neutral material record represents physical density and colour. A source-preserving renderer path needs independently represented asset and appearance parameters, separate model/configuration and holder assignment chronology, and a native-backed allocator rule. Whole-source transfer also needs normalized ownership of the distinct source datum identities and creation events. The constructor experiment leaves every unresolved owner gate in force. The next disclosed native trial can hold an independently generated planar parent and selected child geometry fixed while comparing constructor appearance publication and save against the same-locator baseline.

```sh
PLANAR_VISUAL_PROOF="$(mktemp -d)/Proof"
python3.14 -I -B re/tooling/sw2026/planar_registry/ProvePlanarVisualComposition.py prove \
  --disclosed /absolute/path/to/Oracle121Takeover \
  --output "$PLANAR_VISUAL_PROOF"
```

Only the sanitized numeric receipt enters Kit. The original files and earlier receipts stay in their existing custody. [Tool](../../tooling/sw2026/planar_registry/ProvePlanarVisualComposition.py) · [Owner audit](../../tooling/sw2026/planar_registry/PlanarVisualOwners.py)

The subsequent named renderer composition models the stock resource, independent shader inputs and both fresh appearance allocation events. It replays both disclosed child renderer graphs and preserves these constructor-only controls byte for byte. The new route remains internal while the paired native lifecycle and source creation chronology remain open. [Renderer ownership and guarded comparison](SdkPlanarRendererComposition2026.md)
