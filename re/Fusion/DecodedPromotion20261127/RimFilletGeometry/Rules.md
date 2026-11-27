# Frozen discovery rule for one top circular rim fillet

Owner: `/root/audit_native_evidence`, decided child `A11-RimFilletRead20261127`, parent PR #397. Research only; no production edits, CAD/native API or model calls. This rule derives from the six native `Sources/discovery-01..06/Native.f3d` files. The native bytes of original holdouts, depth-edited holdouts and four post-freeze cases have not been opened for this phase. Historical qualification summaries/measurements had been inspected during the inventory and a one-line manifest read exposed additional measurement metadata during setup; this is a typed-source prediction split, not a claim of wholly blinded measurements or independent topology families.

## Actual source ownership

The ordered native features are sketch, extrusion, `DcFilletEdgeFeature`; the latter has one `DcFilletEdgeData`. The feature-level `rParamRadius` is absent. Radius is `DcFilletEdgeData.radiusValue` resolving to a `DcDoubleParameter`, then its reciprocal `Parameter` with native name `Radius`, millimeter display unit and centimeter numeric values. Both parameter nodes agree and belong to the fillet. `tangencyWeight` similarly resolves to the owned dimensionless parameter, value one. The edge data is constant radius, not chord/asymmetric/G2/rule/variable/full-round; unsupported alternatives and nonempty point arrays must refuse. Its `connectedEdgeRef` equals the feature's sole `targetDataRefs` member, a `ModelDataRef`; that member owns one `BrepRef`, one source `DcBody`, and an `ASMRecipe` containing the full selected edge tag plus adjacent face/vertex recipes.

Join the selected full feature tag (primary, operations, secondary and approach) to exactly one physical predecessor edge. It must be the complete top circular rim at extrusion height, between the cylinder side and top cap, not another coincident or lower edge. Derive operation allocation from the fragment's actual feature-ID manager and source progenitor data, never recorded numeric object IDs or operation IDs. The body UUID, selected DcBody, owner extrusion, current history and feature start/end states must agree. Extrusion end equals fillet start; fillet end equals the current solid state. Source IDs and states vary per archive and are not constants.

Active feature/reference/update owner and component/fragment scope checks must preserve all saved data. Feature, ModelDataRef and BrepRef update health is true in discovery. Radius and tangency-weight dynamic update nodes report false body/predecessor health in these healthy documents; blanket health checks on all parameter updates are invalid. Require their actual owner relationship and declared source parameter state instead. The selected edge alone has a `TrackAttrib` in the predecessor, naming its actual BrepRef; it is not a face tag or a geometry transform.

## Exact geometric construction

Use source radius R, extrusion height H and fillet radius F, in centimeters here, with `0 < F < min(R,H)`, origin `(0,0,0)` and identity XY frame. Set A=R−F and Z=H−F. The final rotational solid has bottom disk radius R at zero, cylindrical side radius R from zero to Z, quarter-torus top rim with major radius A and minor radius F centered at `(0,0,Z)`, and top disk radius A at H. The three unique full circular rims are `(R,0)`, `(R,Z)` and `(A,H)`. Native torus/cylinder axes and references are +Z/+X; the top rim ellipse normal is −Z and the other two ellipse normals +Z. All edge parameters are `[-π,π]`, with coincident end vertex at the geometric negative-X seam; no pcurves or bounded carrier intervals occur. Do not replace complete carriers with sampled geometry.

The complete final solid has one body/lump/shell, four faces, six one-coedge loops, six reciprocal partner coedges, three edges/vertices/points, one torus, one cylinder and two plane carriers. Torus joins side and top tangent rims; cylinder joins bottom and side-tangent rims; caps own their one corresponding circular rim. Bottom face is reversed; the other faces are not. Coedge partner directions and complete face/loop/shell/edge ownership must agree; all original references and entities must remain accounted for. The final body retains six physical tag owners, two bottom-rim sketch-source attributes and one finite body time attribute. The blend face is owned by the fillet operation; inherited side/cap/bottom-rim tags belong to the source extrusion. No guessed geometry-only projection can replace those attribution checks.

## Analytic mass, not a fitted cache

For t=z−Z in the rounded height, radial extent is `ρ=A+sqrt(F²−t²)`. Integrating cylindrical slices gives:

- J0 = A²F + πAF²/2 + 2F³/3
- J1 = A²F²/2 + 2AF³/3 + F⁴/4
- J2 = A²F³/3 + πAF⁴/8 + 2F⁵/15
- J4 = A⁴F + πA³F² + 4A²F³ + 3πAF⁴/4 + 8F⁵/15
- V = π(R²Z + J0)
- Mz = π(R²Z²/2 + ZJ0 + J1); centroid `(0,0,Mz/V)`
- Qx = Qy = π(R⁴Z + J4)/4
- Qz = π(R²Z³/3 + Z²J0 + 2ZJ1 + J2)
- origin inertia diagonal `(Qx+Qz,Qx+Qz,2Qx)`, cross terms zero
- area = πR² + 2πRZ + πA² + π²AF + 2πF²
- bounds `(-R,-R,0)` to `(R,R,H)`

These are exact mathematical integration identities, not regression. Reuse the established `RotaryMass.CacheNumbers` tolerance (relative 1e−6, absolute 1e−8) for saved mass-cache values; kernel cache diagonal entries are slightly asymmetric on rotational controls. Preserve actual `volumePrec/inertiaPrec` values as observations rather than assuming their meaning or widening tolerances from them. Compare the formula independently with recorded API volume/area/centroid/bounds and the existing source-free `SolvePart`/round builder's mathematical result. Generated source-free geometry is an additional implementation cross-check, not new native evidence or a substitute for source selection.

## Snapshot and predecessor correspondence

The saved `.smb` holds the pre-fillet cylinder and separate profile/sketch sheets, not the final fillet solid. Parse the actual member with the existing typed grammar. Join its cylinder body exactly to the predecessor body after validating all live metadata removed by snapshot serialization. `CanonicalBody` already normalizes body metadata and entity tags, but the selected predecessor edge additionally has the validated tracking attribute naming the BrepRef. Remove only that tracking record in a reversible comparison after checking owner and reciprocal attribute links; retain its exact original bytes/state in evidence. Then compare complete rooted topology, every carrier, seam, all face/edge tag groups and source sketch links, with reference ordinals normalized. Do not discard generic tags, sheets, arbitrary attributes or records to force agreement. Validate the two distinct sheet bodies in their actual local XY frame, source circle and source links; demonstrate complete nonoverlapping coverage of all saved records.

This predecessor/snapshot relation differs from the independent-draft snapshot's final-solid relation. Any unexpected tracking, sheet or carrier variant is a retained refusal and a new rule question, not permission to normalize more records.

## Confidence and held-out prediction

Existing typed schemas provide record types/field ownership; six native discovery observations support the declared mathematical relations and selection family. Generic byte grammar is already decoded; no missing-wire-grammar claim follows from absent strict projection. Full attribution and scope admission remain qualification obligations until executable checks and serialized counterexamples pass. Freeze this document and its executable rules before opening reserved native bytes. Replay discovery, then six original parameter holdouts, six independent depth edits and four post-freeze parameter cases without refitting. Record all mismatches, exact hashes/builds, and proposed production helpers. Public reading/writing and native target acceptance remain separate parent gates.
