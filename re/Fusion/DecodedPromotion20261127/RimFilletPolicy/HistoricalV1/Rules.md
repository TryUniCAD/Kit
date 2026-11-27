# Frozen source roles rule V1

This is a typed-source admission experiment, not native acceptance or conversion qualification. Discovery contains six vendor-saved original files; reserved archive bytes have not been opened when this rule is frozen. Existing campaign prose, sibling geometry summaries and the qualification case metadata have been viewed. Native measurement records are historical Fusion `2706.1.17` observations, not newly blinded measurements.

## Source and feature ownership

The sole component's saved creation-order list must contain exactly `DcSketch`, `DcExtrudeFeature`, `DcFilletEdgeFeature`, in that order, and cover every semantic `DcFeature`. Existing assembly, containers, placement, status, untapered blind extrusion, circle, scopes, scene-reference and material gates remain applicable. Unknown classes, unknown saved members, opaque group members, dangling references, unsupported feature flags, non-XY placement, extra bodies/features and unconsumed parameter/reference nodes refuse. Every typed reference is resolved in its original segment; no graph record is removed or rewritten for qualification.

The existing profile gate assumes every `ModelDataRef` belongs to the extrusion. That assumption is refuted here. It is called in scoped mode, then the full graph must contain precisely the profile reference and the independently selected fillet reference. The fillet's sole `targetDataRefs` entry must equal its sole edge-data object's `connectedEdgeRef`. Its `dataRefs` must contain one `BrepRef`, scoped to this asset's component and referencing the one `DcBody`. Feature `childNodes` cover exactly that selection pair and the fillet's two bindings.

## Fillet modes and parameters

There is exactly one `DcFilletEdgeData`; constant-radius/compute-chain flags are true. Asymmetric, chord, flip, G2 and rule modes are false; optional alternative references, offsets and point lists are absent. Fillet type, topology and scope are zero; rolling-ball corners and tangent propagation are true; `rParamRadius` is absent. These mode boundaries derive from saved field vocabulary and are bounded observations, not evidence for other modes.

All four `DcDoubleParameter` nodes are covered by semantic owners: extrusion AlongDistance and TaperAngle; fillet TangencyWeight and Radius. Each binding has reciprocal `Parameter.dcParameter`, exact owner/parent, finite equal values, active/not-edited/not-eliminated state and unique positive `rparamId` within `nextParamId`. Parameter-table coverage is exact. Native length values are centimetres even when display unit is `mm`; neutral values multiply by ten. Taper is zero. Radius is positive and below the source circular profile radius. TangencyWeight is dimensionless one with a literal expression; preserve it as an existing neutral number Parameter owned by the fillet. Existing literal/reference grammar remains unchanged for length/angle. No public permission flag is widened.

## Recipe and cached selection

The selected `BrepRef` points to a version-three `ASMRecipe` containing three singleton tag groups: selected edge plus two adjacent faces. No lightweight tags are present. Complete EdgeRecipe structure, recursive adjacent seam vertex/edge recipe, UV ordering and reference-face flags must match the recorded top circular rim form. Its independent `BrepProgenitor` recipe must be typed-equal, with exactly two ASMRecipe records overall. Tags are never case constants: sibling geometry proof must resolve every full tag group against the prior physical edge/faces/seam vertex.

The selected cached circle must lie at `(0,0,AlongDistance)` in centimetres, have normal +Z, reference +X, full `0..2π` angle and the profile radius. It has no endpoint/edge/progenitor owners and an identity sketch transform. Matrix caches remain identity with no progenitors. Cached topology scopes use the actual same asset/component; IDs are positive. Geometry state, actual snapshot identities and cached topology IDs remain independently validated by sibling geometry proof.

## Dependency, dynamic and allocation ownership

All 17 dependency arcs are derived from semantic role links, including extrusion-to-fillet history and fillet selection/binding dependencies. Predecessor and successor maps must be exact inverses and equal this role-derived graph. Compute order covers all DcNodes once; all manager and creation-order owners identify the actual fragment. Feature-ID maps are reciprocal, cover the three actual features and allocate one sketch, two extrusion and one fillet ID. They are not hardcoded document IDs.

Every DcNode uniquely owns one reciprocal DynamicUpdateData. Feature/reference/tool nodes have both health flags true; DcComponent and parameter nodes have both false. Healthy saved parameters therefore refute a blanket true-health check. Every dynamic predecessor timestamp equals the actual referenced owner's timestamp; empty-body/hash fields and inactive/edited/eliminated guards stay strict. Fragment/parameter/passive/progenitor allocators require unique positive owned IDs bounded by their actual next-ID fields; memory addresses are research bookkeeping, never generated constants.

## Evidence status and remaining scopes

Typed loader grammar is reused rather than inferred from byte offsets. Six discovery files pass the composed policy. Full source/native measurement reconciliation and reserved replay remain required; no claim covers another topology, variable fillets, another frame, non-unit tangency weight, user equations or extra feature histories. Material package reads and scene references reuse existing bounded checks; these do not establish arbitrary appearance/history export. Sibling geometry owns physical tag resolution, history state joins, snapshots and measured mass agreement. Public projection must not be enabled until all these independently agree.

Proposed production modules after approval: `Native/Circular/RimFillet/SelectRim.py`, `ReadRimParams.py`, `CheckRimSelect.py`, `CheckRimManagers.py`, `CheckRimCaches.py` and `CheckRimPolicy.py`. Reuse existing `FilletFeature`, `FeatureStep`, Selection and Parameter records. `SelectRim(Graph)` returns the original ExtrudeContext and original fillet/data nodes. `CheckRimSelect` returns the original selected BrepRef and complete RecipeValue to geometry. No duplicate neutral feature type, donor lookup or source graph normalization is proposed.
