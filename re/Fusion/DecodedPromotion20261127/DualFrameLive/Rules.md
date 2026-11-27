# Frozen XZ source frame and comparison rule

Task: `A11-DualDraftFrame20261127`, research-only child of the decoded read/write promotion. No existing production module is changed by this phase. No native API, model provider, commit or push is used.

This rule is recorded after inspecting only the six committed `frame` discovery archives from `TwoSidedDraft20261127`. `Discovery.json` binds their actual typed graph fields, source hashes and independent API frame observations. The six `holdout_a` archives remain unopened until this rule and its comparison method are recorded. Their earlier numerical measurements in the separate geometry campaign do not make this a wholly independent generator lineage.

## Frame ownership rule

The actual sketch basis comes from its selected `CoordinateSystem.transform`, not a name or a body transform. The selected UCS must belong to the same component; `MSketch.UCS` must resolve to that node. The sketch's reciprocal `rDcNode` must identify the owning sketch feature. That feature's owned `DRMatrix.matrix3d` must equal the UCS matrix, with reference type 2, no inferred/reversed axes, extra offsets or reorientation controls, and zero old rotation.

The DRMatrix must select exactly one `EntityDataRef`. Its recipe resolves to an original `WorkPlane` belonging to the component's actual `OriginWorkGeometry.children`, with reciprocal parent membership and `originName = XZ`, `isOrigin = true`, no driving work-plane feature. The matrix and reference's `rParentFeature` and dynamic-update `rOwnerNode` must identify their actual owners. All passive scopes must match the source asset/component/sketch as the existing `CheckScopes` policy requires. The root component instance, initial transform if present, and sketch occurrence transform must be identity.

The recorded XZ origin datum has U along +Z, V along +X and normal +Y. Its default saved sketch basis is X along datum V (+X), Y along negative datum U (−Z), Z along their right-handed cross product (+Y). Thus the native sketch basis differs from the datum's in-plane axes. Require this bounded principal-plane relationship and validate orthonormality, handedness, origin and bottom homogeneous row; do not accept an arbitrary matrix merely because it is invertible. The saved extrusion `profileNormal` must equal the saved sketch normal.

All six discovery matrices match the API's row-major 4×4 transform exactly. Local profile center `(7, −11)` mm maps to world `(7, 0, 11)` mm. Current values are source observations, never production constants or case lookups. Matrix storage uses centimeters for translation; the neutral frame uses millimeters.

## Rigid comparison rule

Current solid carriers are already in component/world coordinates. Their explicit BODY transform node is identity, which must be validated completely; it must never be replaced by the sketch UCS. Invert the independently selected rigid sketch frame only for a comparison view: subtract its origin for points, then dot with the saved X/Y/Z basis; transform vectors by the same rotation without translation. This maps world cone/cap/rim/point data into the existing local XY validator convention and preserves angular parameters, radii, orientations, all topology references and every attribute/group/source ID.

The preferred production contract keeps every original state record, including a proved identity BODY transform, and validates a comparison BODY view with `TransformRef = -1` only after proving that node. Existing bounded cover checks may admit that one additional identity node without permitting an unknown transform or dropping it. Return the original checked world live state for the snapshot validator. Its profile sheet is world-placed while its sketch sheet remains local, so each must be checked in its own proved frame.

For this research experiment only, a reduced local comparison view may temporarily remove the one certified identity transform after recording it and its exact index. All remaining references must be remapped bijectively. Reinserting that exact record, restoring BODY's reference and applying the forward rigid map must reconstruct the original typed state. The original source/world state remains unmodified and retained. No normalized view is a native output candidate.

## Pre holdout strengthening

After the first six discovery files passed the graph, API matrix and reversible live-view checks, the frame rule is strengthened before opening any reserved file: both DRMatrix and EntityDataRef must be active, unedited and not eliminated; their dynamic-update nodes must report body and predecessor health. These same typed flags are true in every discovery packet. No matrix, identity or geometry relation changes. The original passing discovery receipt and exact earlier rule/script bytes remain in `HistoricalSources`. The strengthened rule will be replayed on discovery and only then evaluated on the six reserved states.

## Confidence and exit

Typed field locations and the selected origin/default basis relationship are observed on six discovery files and measured against their existing API observations. This is a bounded semantic rule using existing matrix/geometry grammar, not a claim of unknown or newly recovered wire grammar. The comparison method still requires execution over complete live geometry, tag/attribute coverage and independent first/second edits. Then evaluate all six reserved `holdout_a` files without changing the rule; retain failures rather than widening it silently.

Only after complete graph ownership, API frame equality, reversible geometry views, live tag checks and held-out predictions pass should the root coordinate production changes. Public admission, saved snapshot integration, unsupported-frame counterexamples, native writer construction and target acceptance remain separate gates.
