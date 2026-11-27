# Source-selected XZ snapshot rule

Task `A11-DualDraftFrame20261127`. This is research only. No production file, native API, model provider, branch or publication operation is changed. The six `frame` discovery archives were inspected; all six `holdout_a` archives remain unopened while this rule is derived.

## Discovery facts

The selected sketch UCS is the typed row-major matrix with columns U=(1,0,0), V=(0,0,-1), N=(0,1,0) and zero origin. The owned DRMatrix stores the same matrix; the extrusion profile normal equals N. The API's recorded profile transform and world circle center agree with that frame. The separately validated frame owner must establish plane-recipe scope, parents, sketch-matrix ownership and identity occurrence/root-instance placement before a public route can use it.

The live solid is already expressed in world carrier coordinates. Its BODY additionally references an explicit identity TransformNode. The snapshot solid has a corresponding identity node, while the double-sided profile sheet owns a second, separately allocated identity node. The single-sided sketch sheet has no transform reference. These are not the selected sketch UCS and must never be replaced by it or applied as a second rotation.

The existing canonical rooted solid comparison is frame independent and agrees on all six discovery archives, retaining the identity transform record. Root closure sizes are 45 for the solid, 14 for the profile and 13 for the sketch; all three closures are disjoint. Compared with the XY family, the two additional records are certified identity transforms. Every record remains covered.

## Proposed complete validation rule

1. Read the frame from the source UCS; require equality with its selected DRMatrix and with the recorded discovery API frame. A public implementation must use the independently qualified source-frame reader, not a per-case matrix table
2. Allow BODY.TransformRef=-1 or an actual TransformNode whose attribute and entity tags are absent, basis is identity, translation is zero, scale is one and rotation/reflection/shear flags are false. Reach and account for the original record. Do not discard or merge it
3. Independently identify solid, double-sided profile and single-sided sketch roots from their linked shells. Keep the existing scoped cache identities, passive scan order, serializer name, feature/sketch attribution, header and complete solid-graph correspondence checks
4. The profile sheet is in world coordinates. Its circle center is O+cx*U+cy*V, plane/circle normal is N, reference/major axis is U, and its seam vertex is center+r*cos(t)*U+r*sin(t)*V. Convert the neutral model's millimeters to native centimeters once. The sketch sheet instead uses its original local XY coordinates and identity frame
5. Retain the existing planar face flags, full-circle periodic interval, seam closure, source circle/split/direction identities and topology ownership checks. Permit exactly one additional TransformNode in a sheet closure only when its BODY owns that record and the complete identity validation passes
6. Require all three closures to remain disjoint and their union to account for every snapshot record except the leading ASM root. Keep the original world live state; never return an inverse-transformed state to snapshot correspondence

## Production extension proposal

Pass the existing neutral `Transform` as the source-qualified Frame to `CheckDualSnaps`. Add a narrow helper that certifies an explicit identity body transform and uses a temporary comparison Body.TransformRef=-1 only for the existing linked-shell walker; retain original records for canonical comparison and coverage. Let the profile-sheet geometry checker consume Frame while the single-sided sketch checker consumes identity. `CheckSnapLinks` and `CheckSnapHead` have no XY geometry assumptions and need no weakened scope or identity guards. Replace the current hard-coded source-UCS identity check with equality to the independently validated Frame; keep occurrence identity.

Confidence before holdout: six-archive source correspondence and source-selected geometry rule confirmed on discovery; holdout generalization pending. Full native conversion acceptance remains unestablished. Missing broader frame/plane grammar is separate work, not permission to accept an arbitrary transform
