# Ordinary planar assembly registry qualification

Task B04-SW2026-ASSEMBLIES-C10, delivery PR #121. This packet prepares a disclosed assembly emitted by the default public `convert.write_document` registry. The root agent owns the single native oracle. Qualification requires clean open, rebuild, active dimension edit, synchronized save, and fresh reopen with healthy brackets and strict typed child presentation checks. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Assembly writer guide](../../../Documentation/Reference/Adapters/SolidworksAssemblyWriting.md)

## Frozen disclosed case

The SDK revision is `2393c3a8106e83ee90e977fb167d27900e5f4f2a`. The ordinary planar registry was registered at `81278b25a8648511540f8809e59a0a3a00607d99`. The disclosed recipe uses the existing two-occurrence boundary fixture. Both occurrences own the same 37.1 × 18.6 × 9.3 mm centered rectangle child, with selected configuration `Child configuration`. The parent uses `Assembly configuration`. The first occurrence is fixed. CoincidentY selects the two Top Planes and DistanceZ selects the two Front Planes. The independently predicted edit is 42 to 57.73 mm. It moves only the floating body along positive Z. Expected native tree counts are 26 parent rows and 25 child rows. Parent COM Z moves from 25.65 to 33.515 mm; volume and area remain 12,835.116 mm³ and 4,832.28 mm². [Independent predictor](../../tooling/sw2026/PortableAsmPrediction.py)

The guarded host preparation passed in five distinct writer processes. The internal public-route preparer supplies a memory witness. The actual default and explicit alias workers reproduced both complete containers and all 22 streams at the same locator and clock. The unqualified-child and stream-destination workers refused without residual output or stream mutation. All five processes had zero runtime input reads. The strict public reader recovered both occurrences, four ordered mate endpoints and three child drivers, with the existing informational `sldasm.native_record_unresolved` diagnostic. Thirteen linked typed streams reproduced exactly in a separate archive audit. [Host evidence](../measurements/2026/SdkPlanarRegistryDisclosedHost01.json) · [Guarded registry worker](../../tooling/sw2026/PublicAssemblyRegistryProcess.py) · [Archive audit](../../tooling/sw2026/ReadSdkPlanarGroupNative.py)

| Frozen item | SHA-256 |
| --- | --- |
| Fixture | `33d6f617549610329ef93badc5ec163264de7a5a5440d9f4bb29c09a09ff5160` |
| 7,431-file SDK and tool manifest | `67513b8292b53282fc0a8c3c874e37dad50aa65095dbd265f6930014739b2cc9` |
| Neutral request | `bda3932b4896eb32315cd3ec26d4ebe2c4b5fb5fae1be47714db6fada7d30816` |
| Independent prediction | `59544973c4d04be8689bff0b7719572ccc913559c59f840ba92d7f28198a4296` |
| `PublicPlanarPair2.SLDASM`, 10,392 bytes | `d31950eb971645908a82c26ecb881880525a3c8aa9478bc971b065bc5bdcf2f4` |
| `PublicDatumPrism.SLDPRT`, 8,714 bytes | `b734fe2b8df59085860ae12f6dacabd363a4475f5399506efdce423d05c4ab7b` |

The typed child check follows `moProfileFeature_c.pd_f80` to the actual `sgSketch` and its `dims.f118` ordered display list. Each `moDisplayDistanceDim_c.f850` target points through `moSkDimHandleValG2_c.ff0/ff8` to the same sketch and the exact D1 or D2 row. Generated text positions are (0, −13.95, 0) mm and (27.825, 0, 0) mm. The comparison retains all three text coordinates, witness endpoints, along and away vectors, placement fraction and offset, under-text mode and centreline route. Non-float values and inventory compare exactly, with an absolute tolerance of \(10^{-12}\) for the finite typed floats. A contrast computes the old explicit recipe's formula on the disclosed dimensions and finds four differing coordinates. The actual A20/A21 source presentation still needs the separate comparison below. [Rectangle presentation rules](SdkRectangleDimensions2026.md) · [Typed presentation comparison](../../tooling/sw2026/planar_registry/RectanglePresentation.py) · [Prior explicit formula](../../tooling/sw2026/OriginalPlanarRecipe.py)

During preparation, initial attempts stopped on the Git archive export filter, an unloaded framework validator caught by the guard, and an origin record that also had a sketch link. The final recipe freezes explicit Python trees, warms neutral validation before the guard starts and selects the actual named profile. The resolved display owner is the serialized list and handle link. Host preflight passed, and the host native-phase request refused before control or working-file access. Native processes, prior source reads and held-out credits are zero.

## Root-controlled native recipe

Reproduction on the pinned macOS Python 3.14.7 interpreter uses an unused host directory. Preserve the final encoded locator so the parent and child share the directory and the verified parent can resolve the exact generated child.

```sh
PLANAR_PACKET="$(mktemp -d)/PlanarPublicRegistry01"
PLANAR_WINDOWS='\\Mac\Home\Documents\UniCAD\Oracle121Takeover\PlanarPublicRegistry01'
python3.14 -I -B re/tooling/sw2026/planar_registry/PlanarRegistryBuild.py prepare \
  --output "$PLANAR_PACKET" \
  --native-parent "$PLANAR_WINDOWS\GeneratedInput\PublicPlanarPair2.SLDASM"
```

The prepared output supplies its exact fixture SHA. Process receipts can change on another preparation. Require the same two complete output hashes at the declared interpreter, locator and event. Transfer the immutable prepared packet to the corresponding unused shared packet directory. Use the previously disclosed A22 `ControlCase.json`, its existing packet digest and the actual Windows locators of `A22CombinedRotated.SLDASM` and its synchronized `CohortChild.SLDPRT`. The observer checks both original CAD file hashes in the guest before and after each native phase. [Preparation](../../tooling/sw2026/planar_registry/PlanarRegistryBuild.py) · [A22 control custody](SdkExplicitPlanarGroupNative2026.md)

```sh
PLANAR_OBSERVER="$PLANAR_PACKET/CodeRoot/re/tooling/sw2026/planar_registry/ObservePlanarRegistry.py"
python3.14 -I -B "$PLANAR_OBSERVER" verify --packet "$PLANAR_PACKET" \
  --fixture-sha256 "$PLANAR_FIXTURE_SHA"
python3.14 -I -B "$PLANAR_OBSERVER" bind-control --packet "$PLANAR_PACKET" \
  --fixture-sha256 "$PLANAR_FIXTURE_SHA" \
  --control-case "$PLANAR_A22_CASE" --control-case-sha256 "$PLANAR_A22_SHA" \
  --control-parent "$PLANAR_A22_WINDOWS_PARENT" --control-child "$PLANAR_A22_WINDOWS_CHILD" \
  --windows-packet "$PLANAR_WINDOWS"
```

The generated `Recipe.json` contains guest argv, in order `before`, `generated`, `reopen`, `after`, `summary`. Prefix each argv with `["prlctl", "exec", "Windows 11", "--current-user"]`. The established Python 3.11 launcher loads registered `pythoncom` from the ordinary user environment. The fresh phases bind executable `34.5.2.0604` and its exact SHA-256. Run `after` even if a candidate phase fails. A missing phase or failed bracket keeps the summary failed. The transport exit and native result are separate receipts. [Observer and recipe](../../tooling/sw2026/planar_registry/ObservePlanarRegistry.py) · [Existing lifecycle](../../tooling/sw2026/InspectCombinedPlanarMates.py)

The generated phase copies only the guarded output pair to its exact unused final paths. It requires a clean native open/rebuild, actual component and datum references, the exact complete predicted tree, all three child driving values, a real DistanceZ edit and zero-error/zero-warning child-first save. The next process checks the saved hashes, child path and stamp, edited distance, geometry, quality and complete tree. It observes the typed saved rectangle displays before and after verification of the saved native identities, reports each presentation difference, runs strict public readback and re-emits the 13 scoped linked streams. The summary requires four independent native process births in order, both controls, retained identities and all strict phases. A control or candidate that changes or loses a scoped owner remains a recorded failure.

## A20 and A21 prior-cohort registry comparison

The original source lock was committed at `f4b5e1a9b93dc679bb32dd7f2fe141b47bd58398`, before the internal planar constructor `a06b6d4ef0aa7f185e5e9ac8b82803dc159aa583`. The first source comparison method was frozen at `986fea15c67c044afda3f6ccc5d62966b7bb819e`; the measured internal A20/A21 lifecycle is committed at `f1e608a7d1227786e32f978a504e8ef855302353`. It has 26/25 and 27/25 actual tree rows and 440/552 numeric checks across ten fresh processes. These are prior measured sources. A default-registry comparison adds zero unseen designs. [Source lock](../v2026/heldout/AssemblyPlanarMateSourceLock01.json) · [Prior native result](SdkOriginalPlanarMateNative2026.md)

Proceed only after the disclosed packet passes. Use the existing guest-only release and custody from `RunOriginalPlanarEvaluation.py` in separately named work directories. Check the same original parent, synchronized child and original author specification hashes before strict public read of each source. Call `PlanarPriorAdmission.source_intent` with the strict source document, that authenticated case recipe and the actual locked child bytes in a source-reading process. The helper accepts only the exact two prior custody pairs, the closed case envelope, one fixed occurrence, the actual centered Front-plane 40 × 20 × 10 mm child, canonical principal datums and the ordered coincident/distance or parallel/distance roles. It uses the existing source projection to compare the real configurations, rigid placements, selected occurrences and supports, ordered child drivers and ordinary system inventory. A source folder, cabinet, origin or plane label the normal writer cannot preserve causes refusal. The real mate and occurrence names enter a fresh portable document. Source display evidence stays in the source supervisor. [Prior custody and evaluator](../../tooling/sw2026/RunOriginalPlanarEvaluation.py) · [Exact source intent gate](../../tooling/sw2026/planar_registry/PlanarPriorAdmission.py)

Freeze that document and the independent original/edited predictions before handing the fresh writer process only neutral JSON, event and its new exact Windows destination. Reuse the guarded default registry worker and its same-route memory witness. Compare the actual ordered D1/D2 display fields in the locked original and actual generated child using the typed comparator before native dispatch. A difference is a failure of the source presentation gate with the exact path and two values recorded. Continue a separately labelled geometry diagnosis only under an independent observation plan. The prior explicit formula does not supply source display values. [Guarded writer](../../tooling/sw2026/PublicAssemblyRegistryProcess.py) · [Typed ownership and comparison](../../tooling/sw2026/planar_registry/RectanglePresentation.py)

A passing source gate still requires the original/actual generated tree, placement, mass and geometry comparisons of `InspectOriginalPlanarSlot.py` and fresh A22 brackets. Require the actual distance owner and edit, saved child path and stamp, strict generated and saved public readback and original/generated/saved child presentation parity. A20/A21 recipe generation, native regression and any input with additional presentation, nested ownership or broader features remain outside this disclosed result. [Prior native observer](../../tooling/sw2026/InspectOriginalPlanarSlot.py)
