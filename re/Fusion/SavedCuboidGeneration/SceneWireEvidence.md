# Structural graphics wire boundary for fresh cuboids

[ProbeSceneWire.py](ProbeSceneWire.py) measures a minimal in-memory OGS scene on an exact, previously generated constructor archive. It requires the caller to pin the input digest. It does not publish an archive, graphics stream or viewer artifact. [GenerateSemantic.py](GenerateSemantic.py) remains the separate source-free constructor.

## Derivable structure

The Design body owner comes from the actual `DcExtrudeFeature → DcBody → Body` references resolved by `SelectExtrusion(BuildGraph(document))`. The writer can also resolve this identity directly from `DesignResult.Roles` after `BuildDesign`. In the three measured constructor archives the graphics target is Design `(0, 1140)` and the ASM history body key is `0`. In the measured prior native lifecycle, the Design owner was stable across the edits while the history body key changed. The `actIdentifier` text agrees with the segment and object pair, but does not establish that the graph has a body ACT revision row. The three fresh files have no such row. The native saved files used for comparison do.

The [leaf plan](LeafPlanEvidence.md) provides the canonical physical history slots and current solved boxes for 12 edges and six faces, plus the separate logical face chain. The probe derives `BrepWorld.ModelBox` from the current frame at fresh construction. It binds the body group to the actual Design entity, adds zero-LOD structural leaf boxes, and uses a single generated scene-local handle. The handle is an OGS `ObjectRef`, distinct from the Design `EntityRef` and ASM body key. Using the Design object number as the one local handle is an isolated probe convention. The format only requires a valid, nonzero unique handle in this one-object scene.

## Verified SDK boundary

| Source-free case | Constructor archive SHA-256 | In-memory world SHA-256 |
| --- | --- | --- |
| Baseline | `ed4bfd74de13a08b726bb019629a1707a9eb4549c43a06707048be590164a6be` | `88dad72f152342a0975e45aef6eb39c6671dc97b5e490223d4bbdd1cfb9fdeb3` |
| JSON height edit | `8a28cf09b4e48108ca475d468b9e477314b92dfe1dedbf0715920ab0712682e3` | `6b2edea9a7a570e1aeb805ea19f44582a8f620b4e3f166c8ac5d20274958e85d` |
| Post-freeze holdout | `f318fd94e17b42603c93135d9d6fde7691e5050f950edeee29d4be0d7a5d52b0` | `c1e12141fbc479138bdad408f8725b10eb4cc9344b7f358ea3cf6d694d1d3e1e` |

All three produce a 1,723-byte world and zero mesh streams. `ReadGraphics` reconstructs each typed scene exactly. The lower document codec also round-trips the complete combined typed model in memory. An invalid scene target is refused for all three. Every original archive passes strict public projection as constructor native-state version 1. Adding only the scene takes the public reader into the auxiliary-bearing saved profile, where it refuses the constructor parameter index with `Native fixed rectangle parameter index disagrees with its table`. This refusal stands even though the scene references and lower-level document state pass their checks.

From the checkout root, run with Python 3.14 and the checkout SDK on the module path. Repeat `--case ARCHIVE SHA256` for the other generated inputs. The exact local artifacts are listed in the [oracle preparation notes](GenerationOraclePlan.md).

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedCuboidGeneration/ProbeSceneWire.py --case `
  ../FusionSavedCuboidGenerationOracle01/baseline/Candidate.f3d `
  ed4bfd74de13a08b726bb019629a1707a9eb4549c43a06707048be590164a6be
```

Two fresh invocations over the three listed inputs in that order returned byte-identical JSON report SHA-256 `fd3efd7ffcb117e960b99e35e2e9fefa2796973b54a30db7788f25abe64d720b`. A separate wrong-digest probe refused before opening the candidate.

## Boundaries for the next writer step

The structural contrast uses empty leaf payloads to isolate framing and entity joins. A qualified graphics candidate needs real leaf identity, presentation and selection behavior. Native saves give each leaf the same Design body target and distinct qualifiers. The four edited and restored lifecycles measured face then edge qualifiers `72–89` and `108–125`. Face feature tags stay unchanged, all eight typed history tracking tables are empty, and each Design body retains `edgeSelection=true` with no body-level `passiveIdGenerator` reference. The checked holdout leaf attribute sets carry no selection key. Neither feature tags nor physical slots alone establish a qualifier allocator. Keep the synthetic OGS handle, neutral probe flags and empty payloads confined to this contrast.

The next experiment needs an initialized same-document repeat at each height and a one-factor height edit, followed by face-specific appearance and selection observations before rebuild. Compare leaf qualifiers, ordered bounds, stable Design owner, existing BRep tags and the resolved selected face. Establish the minimum supported style and reference bindings independently of the shape. A future constructor-plus-scene path also needs strict public readback that checks the complete generated constructor and scene together. No public admission was changed, and this work did not run Fusion or measure rendering, selection or native acceptance.
