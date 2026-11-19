# Neutral concentric face admission

Task `B04-SW2026-MATES-CONCENTRIC/neutral-admission`; owner `assembly_occurrence`; delivery PR #121. This host-only research projector connects authored neutral mate selections to actual generated child and kernel objects. It adds no SDK source change, public admission, native acceptance or held-out credit. Root owns wire wrappers, complete parent composition, the VM and later qualification. The base source is `0f571dad8f21624553aa6fef298d629d6b36e55e`.

[Receipt](../measurements/2026/ConcentricNeutralAdmissionSdk01.json) · [Projector](../../tooling/sw2026/ConcentricNeutralAdmission.py) · [Complete B-rep guard](../../tooling/sw2026/CheckConcentricNeutralBrep.py) · [Replay](../../tooling/sw2026/RunConcentricNeutralAdmission.py) · [Authored inputs](../inputs/ConcentricNeutralAdmissionCases01.json)

## Real neutral owners

The existing [mate entity](../../../src/interchange/assembly/MateEntity.py) already stores the actual root definition, ordered direct occurrence path, explicit source entity ID, optional frame and radius. A concentric constraint retains aligned or anti-aligned intent. The [public reader](PublicConcentricMateRead2026.md) places actual rotation lock in the Boolean `rotation_locked` attribute. The projector consumes that one semantic attribute and refuses native diagnostic fields. It does not infer a face from a radius, nearest point, display caption or saved face index.

The normal `ReadAsmModel` stage is reused unchanged. It requires one complete owned repeated child, exactly two direct rigid visible unsuppressed occurrences in this narrower profile, explicit order, actual selected configurations, one group and one fixed anchor. The normal public planar rule/end preparation and circle-child compiler remain unchanged and continue to refuse these documents. This is a mate-intent projection, not complete native document preparation.

Two separately named source profiles are admitted:

| Profile           | Explicit owner                                                                                                    | Required selection                                                                                                          |
| ----------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `authored_brep`   | The supplied child's actual complete analytic B-rep and selected lateral face                                     | The entity's `source_entity_id` must equal that actual face ID                                                              |
| `derived_feature` | The complete ordinary B-rep computed by existing `BuildCircular` from the real feature, support, circle and depth | The caller must explicitly supply the exact canonical lateral face ID; absent, cap or arbitrary native-index strings refuse |

For `BodyId = body/round`, the canonical ID is `body/round-sweep-side-1-face`. This follows `BuildCircular`'s meridian `(0,0), (r,0), (r,d), (0,d)`, `BuildFullSweep`'s body-derived prefix and `BuildFullFaces`'s side index. Edge 1 is the cylindrical meridian segment. It is not a saved native face number. This proves a meaningful feature-only selection without requiring a cached B-rep in every authored child. Caller-owned B-rep IDs may all be renamed when the complete owner bijection remains unambiguous.

## Executable API

```python
binding = bind_cylinder(child_document, actual_part_candidate, generated_kernel_nodes, profile="derived_feature")
intent = project_concentric(assembly_document, {actual_child_definition_id: binding})
```

`binding` retains the actual neutral document, actual `PartCandidate`, typed kernel nodes, neutral B-rep/face/surface, actual child kernel face/surface, body atom and producing feature. `intent.ends` follows `mate.entity_ids` exactly and retains the real entity and occurrence objects. Each endpoint supplies the native metre point/radius and dimensionless axis, plus its actual existing `ReadAsmPlace` placement. The output also retains the complete source document/model, fixed index, alignment code 1/2 and explicit rotation lock. No writer or file path is returned.

The current generated kernel producer is bounded to one uncut diameter-driven forward Front blind cylinder. Binding requires its actual root/header/configuration, complete profile/boss history, real circle point/arc aliases and actual display/handle/dimension/parameter owners. Actual `ATOM_ID_2001` must agree with the shared manager/output atom. The side's `FACE_ID_2001` must agree with the actual extrusion ID, its first `DatumTime` epoch and the real arc permanent marker. Both cap identities must retain their real producing feature and epoch. These are existing [generated attachment](CylinderArchiveAttachment2026.md), [face identity](ConcentricFaceIdentity2026.md) and [typed kernel](ConcentricKernelFaceIdentity2026.md) rules, not new captured values.

| Input                | Derived projection or required guard                                                                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Root and child units | Explicit millimetres; kernel geometry and native translations use metres                                                                               |
| Endpoint radius      | Explicit finite numeric millimetres matching its actual selected child surface; Boolean, missing or metre-valued substitutes refuse                    |
| Occurrence matrix    | Existing portable column-vector millimetre matrix goes through `ReadAsmPlace` to the native row-vector metre frame; scale, shear and reflection refuse |
| Face origin and axis | Actual typed child cylinder, transformed through its own occurrence; no endpoint frame is invented                                                     |
| Selection order      | Exactly the authored two entity IDs and their actual distinct occurrence paths                                                                         |
| Alignment            | Explicit aligned/anti-aligned maps to existing native 1/2; unknown or contradictory initial geometry refuses                                           |
| Rotation lock        | One exact Boolean attribute; current relative twist and both authored rigid placements remain intact                                                   |
| Anchor               | Exactly one actual fixed occurrence from the unchanged normal owner model                                                                              |

The initial two cylinder axes must agree with alignment within the existing `1e-10` dot-product tolerance and have squared coaxial residual at most `1e-20 m²`. The projector does not solve or change an unsatisfied pose. Locking is passed as intent; no zero-twist convention or native lock behavior is invented.

## Complete supplied geometry guard

The first 36-process method checked structural validity, the cylinder carrier and both cap carriers. That was insufficient as a source-preservation gate. Independent mutations to a ring radius, edge interval, edge tolerance, shell order and an additional ring still report zero generic B-rep validation errors. The first method and its exact tools remain frozen separately as discovery evidence.

The final method reconstructs the entire ordinary analytic B-rep from the actual neutral feature. It compares every record in every table, in reference dependency order, after an unambiguous neutral-ID mapping. Every field participates in equality: curves, radii, parameter intervals, tolerances, points, surfaces, senses, loops, coedges, face uses, shells, regions, bodies, transforms and extensions. Missing/extra rows, ambiguous matches and unsupported but geometrically equivalent encodings refuse. Storage-table reordering and arbitrary entity-ID relabeling pass when all actual references retain the complete graph. The seven positives each compare 27 real identities.

A temporary `brep=None` view only invokes the existing plain feature-plan checker. The original supplied document remains in the result, and its complete B-rep must pass before an intent is returned. This is not certification of a stripped model. Native reader diagnostic/provenance attributes are not erased to force admission. Occurrence provenance/extensions fail through the reused normal occurrence guard; selected neutral graph provenance/extensions fail explicitly.

The neutral reconstruction uses outward cap normals `-z/+z`. The native kernel has its own carrier-plane/sense representation. Those domains remain separate; lateral point, axis and radius are checked directly against actual typed generated geometry.

## Exact host evidence and limits

The final frozen proof passes 45 fresh SDK processes: fourteen positives, seven exact independent repeat pairs and thirty-one negative inputs. Both source profiles cover aligned/anti-aligned, free/locked, reverse endpoint order and either fixed anchor. One supplied B-rep relabels every entity ID and reverses storage tables. All fourteen positive processes pass normal neutral JSON encode/decode, retaining the actual selected child/face/occurrence semantics. No runtime file open, process launch or network connection is attempted during generation and projection after explicit source/codec/validation imports. The SDK and research dependency snapshots, tools and inputs remain unchanged.

The scope remains one generated child reused twice. Distinct children, arbitrary imported native face IDs without a real neutral owner, alternate cylinder construction, additional mates/configurations, native diagnostic extensions, alternative trims, noncoaxial starts and general body attribution are unqualified. The supplied B-rep comparison is exact at the typed-field level after ID mapping; it may refuse equivalent geometry with different rounding or representation. No native file or source corpus contributes construction values. Root's later complete assembly/native work is separate.

[Whole-geometry gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/NeutralCylinderFacesRequireCompleteGeometry.md) · [Change entry](../../../Documentation/Changes/Solidworks/Construction/Assembly/Mates/SolidworksConcentricNeutralProjection.md)
