# Proposed bounded reader production interfaces

No production implementation is included in this research child. Root approval and exact path coordination remain required. Policy worker owns source graph/parameter/scope/material/scene validation and the proposed `RimContext`:

`Extrusion: ExtrudeContext`, `Feature: NativeNode`, `EdgeData: NativeNode`, `SelectedRef: NativeNode`, `Recipe: RecipeValue`, `Radius: NativeNode`, `RadiusParam: NativeNode`, `Weight: NativeNode`, `WeightParam: NativeNode`.

Reuse the existing `FeatureKinds.FilletFeature` and serialization; root owns neutral feature/selection/dependency/output-body projection and dispatch. No new duplicate fillet definition, shared snapshot worker changes, shared `RotaryMass` tolerance edits or writer admission are proposed.

## Generic analytic geometry

Root owns `src/convert/Geometry/Fillet/Circular/` and its implementation. The geometry worker owns only the new native adapter directory and geometry archive tests.

- `BuildRimFillet.py`: `BuildRimFillet(BodyId, RadiusMm, HeightMm, FilletMm)` returns complete analytic `BrepModel`, volume, area, centroid and bounds for the bounded identity-XY, origin-centered cylinder with one convex top circular fillet
- The existing `FullRings`/`FullFaces`/`BuildSweepModel` topology with the analytically replaced quarter-torus carrier provides: three exact full-circle boundary rings, two planes, one cylinder and the quarter torus; reuse existing circle/ring, surface, topology construction and complete BRep validators, never source geometry lookup or sampled rings
- `RimMoments.py`: exact slice integrals from `RimMath.py`, including all six world-origin tensor entries in mathematical units; validate positive finite dimensions and `0 < F < min(R,H)`

The existing round constructor independently matches all 22 volume/area predictions but its serialized native archive is not input to this builder. Every generated value must follow dimensions and analytic geometry. General profile/operation/frame admission and source-free native writing are not part of this child.

## Native source geometry, attribution and snapshots

Proposed exclusively owned directory: `src/convert/adapters/Fusion/Native/Circular/RimFillet/`, cooperating with the policy worker's source context without changing its source selection.

- `CheckRimLive.py`: `CheckRimLive(Model, Graph, Context: RimContext, Shape: CircleShape) -> tuple[GeometryState, GeometryState]` returns the complete **original** predecessor and current states; checks original history/state/body association, complete geometry/topology, operation/progenitor/tag and attribute ownership, physical selected edge/face/vertex recipe witnesses, and existing source sketch links
- `CheckRimGeo.py`: full carrier, seam, closed-loop and partner/winding/owner coverage from `RimState.py`; retain every original record and fail on an extra carrier, placement, tag or attribute variant
- `CheckRimTags.py`, `CheckRimLinks.py` and a focused recipe helper: derive physical roles and operation identities from actual validated source graph/progenitors/recipe, not fixed object IDs or operation IDs; current inherited tags and newly owned blend face must remain distinguishable
- `CheckRimSnaps.py`: `CheckRimSnaps(Model, Graph, Context: RimContext, Shape: CircleShape, Prior: GeometryState) -> None`; parse/preserve either optimized cylinder or generic geometry representation, validate the complete source-selected cylinder snapshot and both profile/sketch sheets, and compare against the **prior** solid, not the final fillet body
- `CheckRimTrack.py`: certify exactly one actual selected-edge tracker naming `Context.SelectedRef.ObjectId`, validate its complete reciprocal chain, and make only a reversible comparison normalization; original state remains retained; no arbitrary tag/attribute stripping
- snapshot serializer/passive-ID roles reuse existing `CheckSnapLinks` unchanged. The initial suspicion of added topology caches was refuted: topology caches remain exactly two (extrusion tool solid and region profile); selected-reference caches add a matrix and circle, which the policy worker accounts for in its complete seven-cache inventory
- `CheckRimMass.py`: `CheckRimMass(Context: RimContext, RadiusMm, HeightMm, FilletMm) -> None`; retain original volume/area/centroid and raw origin-diagonal checks, then verify all central diagonal/offdiagonal entries through the mathematically coupled actual centroid/volume, using **unchanged** `CacheNumbers` throughout

The new coupled tensor rule is a post-rim-exposure hypothesis with separately frozen prediction on six translated XY/XZ native controls from another campaign. The original eleven near-zero origin-product refusals remain evidence. Actual API measurements in the rim pack do not contain independent inertia measurements; the saved body cache, existing origin-tensor convention, six separate native sources and thirteen serialized tensor counterexamples are the recorded tensor evidence. Earlier familiarity with the independent cohort is disclosed.

## Verification boundary

Current research proves all 22 source geometry/topology/attribute and prior/snapshot/sheet relationships, requested dimensions, measured API volume/area/centroid/bounds/topology, and mathematical source-free round-builder agreement. The original frozen software first exposed a generic-snapshot convenience-model gap; its failed outcomes remain retained. Corrected representation checks and complete recipe-group checks are additive post-exposure validation, not a new holdout.

Strict production admission additionally requires the policy worker's full graph/parameter/scope/selection cache/material/scene proof, the generated neutral BRep's complete validity/geometry checks, real archive SDK/CLI process integration and serialized refusals on that public route. Root owns revision-bound replay, CI/review, documentation and register changes. Native writer generation/editing and application acceptance remain unfinished. No completed reader or conversion claim follows from these research interfaces.
