# Ordinary assembly lightweight datum data

Task `B04-SW2026-MATES-CONCENTRIC/lightweight-datums` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The scoped `Contents/Config-0-LWDATA` member holds an update stamp, resolved model bounds, a named section hatch and three principal plane caches. Twelve disclosed SOLIDWORKS 2026 SP05.2 members replay exactly through the typed codec. Eleven nonempty parents independently reproduce the whole member after canonicalizing two ignored transform padding words. [Proof receipt](../measurements/2026/D01AssemblyLightweight01.json) · [Earlier omission and save paths](ConcentricAssemblyCacheOwnership2026.md)

## Native model ownership

The original `doccplu.dll` save calls `moLWdataHelper_c(moModel_c*)` at `0x1800301a8` and its `Serialize` at `0x1800301c0`. It obtains the actual opened model from the selected configuration and names the member after that configuration's own storage. The exact AMD64 model image SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The helper's direct, untagged body uses its own archive object map. The receipt binds the complete functions, import pointers and virtual table cells for the 34.5.2.0604 build.

| Member order | Source and rule |
| --- | --- |
| `f70` | Constructor `0x4c790444` calls the actual assembly's slot `0x1030`. It points to `moFiledConcept_c::getUpdateStamp` at `0x4bdac640`. The signed stored value equals both header `f40` values across all 12 sources. |
| `f08` | Constructor `0x4c7903bb` obtains the box with assembly slot `0x1350`, `moAssembly_c::getBBox` at `0x4b6960c0`. The helper writes the ten-double `mgBBox_c` record. Both actual root boxes `f1a18` and `f1a20` agree with this record across 11 nonempty parents. The empty control stores the separately documented unset constructor box. |
| `f68` | The constructor tests assembly slot `0x1a0`. Its assembly implementation returns false, so the stored double is positive zero. The part-specific parameter getter is outside this profile. |
| `f60` | Assembly slot `0x15f0` binds the lazy `getXhatch` at `0x4b69ed30`. With no existing hatch it resolves localized resource `0x3c2c` and initializes constructor angle, scale and flags. The existing English default recipe names the resource `ANSI31 (Iron BrickStone)`. The helper makes a distinct `gcXhatch_c` from that actual model hatch. [English constructor resource](SdkDefaultPartRecipe2026.md) |
| `f78`, `fc0`, `f158`, `f110` | Four embedded `suObList` owners in this exact order. Their constructor scans the current model's actual planes, axes, connection points and route points. Only the plane list is populated in the disclosed cohort. Its three distinct `moLWPlaneNodeData_c` records follow the actual resolved owner order. |
| `f108`, `f10c` | The constructor at `0x4c79081b` through `0x4c790895` separately tests whether the actual model partition and the kernel environment's permanent partition contain bodies. The scoped constructors have no local partition, and the modeled empty permanent environment follows all 12 observed cases. Populated partition state refuses. |
| Two trailing vector counts | The reference-point and coordinate-system vectors have independent signed counts from their actual lengths. Both are empty in this family. Their two separate nonempty object paths remain open. |

## Principal plane projection

The plane-cache constructor at `0x4c78fed0` binds the actual datum through the feature base at `0x4c78fc50`. The base reads its concrete class, name, feature ID, suppression and inverse visibility. The admitted datums are hidden, unsuppressed and have the ordinary default-plane data class. Its point, signed normal, transform, data type and ordered borders come from the actual datum. A native `getBBox` dispatch at `0x4c78ff87` reaches the four-corner path at `0x4c2e33e6`. The separate border accessor at `0x4c2e3570` returns the four real display extents.

The shared native automatic-size rule projects the midpoint of the active assembly extrema onto the canonical datum plane and computes each half span as `span*0.5 + span*0.05`. The ordered tangent frame gives the four corners and the actual name anchor. The corner extrema give the plane's full ten-double box through the shared `MakeBox`. These formulas independently agree with the 33 occupied native datum caches and their actual `ResolvedFeatures` owners. [Native automatic sizing](LocalLinearPatternFiniteHinge2026.md) · [Named corner order](LocalLinearPatternPlaneDirectionRule2026.md)

The plane serializer at `0x4c792077` calls the 120-byte `mgXform_c` operator. Its matrix entries, cache bit, translation, scale and flags derive from the checked canonical datum transform. Native bytes differ from the canonical projection in exactly eight bytes for all 11 nonempty source members. They are word 19 of each of the two nonidentity transforms, an ignored alignment word. The independent projection supplies zero; the source-only decoder retains the actual wire words for forensic replay. [Operator versus compact layout](GeometryArchive2026.md) · [Canonical zero padding rule](SdkDrivingDistanceConstruction2026.md#knowledge-and-field-classes)

## Controlled offline composition

The [reproducer](../../tooling/sw2026/para/concentric/ProveD01AssemblyLightweight.py) checks the pinned original container digests before source reading. Two independent stdin-only workers reconstruct the complete earlier 35-stream D01 parent byte for byte and the exact linked child. The opt-in 36-stream research variant sizes the three currently unset canonical displays on the actual generated model, reserializes `ResolvedFeatures` and adds the coherent lightweight member. All other 34 parent members and the complete linked child remain exact. Fresh typed readback reconstructs the member from the linked owner graph and retains the actual concentric mate. A separate 17.37 mm axial placement contrast keeps its neutral-model child unchanged and repeats the same linked checks at a different extent. Five checks refuse ambiguous or unsupported models and both workers report zero external accesses.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01AssemblyLightweight.py \
  --disclosures /absolute/share/Oracle121Takeover \
  --native-dir /absolute/licensed/module/directory \
  --output /tmp/UnusedD01LightweightReceipt.json
```

This is model-only offline evidence. The ordinary resolved writer still follows its exact prior paths. Lightweight open and graphics behavior, empty-assembly autosizing, authored non-default datum visibility and border values, other locales, additional datum families and unsupported physical partition states remain separate qualification work.
