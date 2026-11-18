# Saved ordinary radial sketch ownership

Task B04-SW2026-CONSTRUCTION, owner `/root`, PR #121. The native-saved
configuration and manager dependencies are pinned in
[SavedPartMetadata2026](SavedPartMetadata2026.md). The typed resolved graph
now reaches the physical arc, its handles and both constraints.

| Native owner | Read rule and evidence |
| --- | --- |
| `sgArc` and `sgArcHandle` | Embedded arc inherits the typed segment record. Three indices use the native short/extended rule. A schema-one arc handle calls inherited `sgEntHandle::Serialize`. Reuse of one endpoint establishes a circle. [Arc and handle field order](CurvedSketchConstruction2026.md) |
| Construction and contour | In pinned `sldmodu.dll`, `sgEntHandle::isConstructionGeom` at `0x4c5cdaa0` resolves its entity and tests bit 0 of `f54` at `0x4c5cdac3–0x4c5cdaca`. The measured curves have the bit clear and registered contour `fd0=1`. Centre and seam coordinates yield the geometric radius. |
| `sgCircleDim` and `moLengthParameter_c` | The value-dimension serializer at `0x4c59ec10` retains both handle slots. Kind 3 is radius and 15 is diameter. The live drive comes from its parameter's `f58` in metres. [Native value and parameter ownership](CurvedSketchConstruction2026.md#radius-and-diameter-dimension-construction-partial-graph) |
| `moDisplayRadialDim_c` and radial display handle | The concrete display inherits its base and stores the typed radial suffix. Its virtual selectors for offsets `0x8a8/0x8d8/0xa78` are zero/one/one. The actual display handle returns to the same sketch and value-array index zero. The allocated value cache uses binary64. [Radial display lifecycle](RadialParameterLifecycle2026.md) |
| The centre's logical dimension | The typed type-17 logical relation follows its point handle to the arc's actual centre index. The neutral fixed constraint references that point. [Centre fixation](CircleCenterFixation2026.md) |

The frozen 4,481-file SDK source closure reads and writes complete
ResolvedFeatures and preserves the full map across twelve disclosed native
saves. All cases retain a typed radial cache allocation. In nine cases the
public adapter preserves one closed nonconstruction circle and both linked
constraints, including both radial modes after native edits. Earlier public
circle IDs remain stable. The three reversed Right-plane boss cases preserve
the raw typed graph and use the existing public fallback for their extrusion
semantics.

The [receipt](../measurements/2026/SdkSavedRadialRead01.json) binds the exact
bytes, source identities, map counters, radial values and public projection
status. The edited circle, saved metadata and combined mate integration
regressions passed on the same closure. These are saved-file reader results.
