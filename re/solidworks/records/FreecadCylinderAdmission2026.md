# FreeCAD cylinder source admission and construction gaps

Task `B04-SW2026-FREECAD-CYLINDER` belongs to `/root/assembly_occurrence`. Root owns integration and native testing in PR #121. Scope is the two disclosed FreeCAD 1.1.4 full origin `Part::Cylinder` files and their complete strict portable projections. Dependencies are the source deck, native companion receipt and SDK snapshot at `47dd6ab67598eb7cdafe8b6595ba19ba2f7da355`. The exit condition remains generated native output that preserves the admitted source owners and passes independent held-out open, edit, rebuild, save, fresh reopen and strict geometry checks. This tranche does not meet that exit condition.

The [admission receipt](../measurements/2026/FreecadCylinderAdmission01.json) records 30 independent SDK processes: two normal strict FCStd reads, four historical/current typed projections, four actual preparation and registry refusals, two exact repeated predictions and eighteen malformed-source refusals. All pass their declared host gates. Fifty independently computed volume, area and centre-of-mass values match the already published native source measurements. New CAD processes, held-out reads, generated native files and emitted SLDPRT bytes are all zero. No primitive writer was started because independently native-authored held-out source locks are still absent.

## Complete source ownership

Both files contain one authored native object named `Cylinder`. Its actual labels are `CylinderA feature` and `CylinderB feature`. The document labels are `CylinderA` and `CylinderB`. `Native.BuildBodies` synthesizes the portable `Body` / `freecad:body:default` when no authored Body container exists. The audit preserves that name and identifies its generated origin.

Each actual feature has thirteen driving parameters, in native property order. The SDK's `FeatureMut` creates them from scalar properties, retaining the native property tree in each parameter's attributes. The audit retains the decoder's recorded `driving` role for all thirteen parameters.

| Property           | Portable kind and unit | Observed ownership and next mapping                                                |
| ------------------ | ---------------------- | ---------------------------------------------------------------------------------- |
| `Angle`            | angle, degree          | Actual full-sweep driver with editable native mapping open              |
| `AttacherEngine`   | string                 | Retains the selected enumeration label and full label list. Mapping is open.   |
| `AttacherType`     | string                 | Retains the attachment-engine identifier. Mapping is open.                         |
| `FirstAngle`       | angle, degree          | Retains the actual source driver. Mapping is open.                                        |
| `Height`           | length, millimetre     | Independent input for a forward blind depth with source parameter ID and name |
| `Label`            | string                 | Binds the producing feature name and retains the explicit parameter owner    |
| `Label2`           | string                 | Retains the secondary label. Mapping is open.                                      |
| `MapMode`          | integer                | Retains the actual attachment selector within the observed inactive mode                     |
| `MapPathParameter` | number                 | Retains the attachment-path value within the observed zero mode                    |
| `MapReversed`      | Boolean                | Retains the attachment reversal field within the observed inactive mode                    |
| `Radius`           | length, millimetre     | Independent input for a radius-driven circle   |
| `SecondAngle`      | angle, degree          | Retains the actual source driver. Mapping is open.                                        |
| `Visibility`       | Boolean                | Retains the actual visibility driver. Mapping is open.                                    |

The source's `Placement` and `AttachmentOffset` are validated independently, including all recorded quaternion and axis-angle components. The measured member is origin-aligned with identity rotation. The actual empty attachment support, empty expression engine, active configuration and absent overrides are checked. The authored source has no sketch, support datum, Boolean operation, assembly or drawing. No such owner is invented in the source projection.

The original native object occurs in the feature definition, feature attributes and document metadata. All three copies must agree. Every parameter must retain its actual path, property type, property tree, ID, name, role, owner and value. Full metadata, native property order, body attributes, shape-material reference and source identity remain bound by independent hashes. The hash keeps those owners in scope for native mapping.

## Historical and current strict reads

The old source deck binds strict JSON without a portable B-rep and with two native document/binding payloads. A normal strict read at this snapshot additionally exposes the actual OCC shape payload and an owned B-rep: one body, one solid region, one closed shell, three faces, three surfaces, three curves, three edges, two vertices and six coedges. The source FCStd bytes are unchanged.

The historical and current projections have identical source feature, configuration, parameter, placement and analytic input values. They have separately recorded JSON and full-document hashes. The current B-rep is retained and correlated rather than deleted to satisfy the existing plain-circle guard. The audit checks its actual cylinder radius, cap heights, complete circle intervals, seam interval, body link and paired edge ownership. It preserves source face IDs and senses. The actual lateral carrier has axis `-Z`. The independent analytic construction uses a derived `+Z` analysis frame. This does not establish a face-ID or parameterization mapping to a new SOLIDWORKS kernel.

The whole source material owner is also retained. A `ShapeMaterial` reference is present even though the portable material list is empty. This audit neither assigns a material nor treats the unresolved reference as proof of unassigned material.

## Nearest construction boundary

The actual public writer refuses both complete current documents with `AdapterNotFoundError`. Direct `PrepareNative` refuses the extended source state before any native byte is written. Further independent, code-bound gaps remain:

| Existing SDK owner                    | Reuse and required boundary                                                                                                                                                                   |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BuildCircular`                       | Reused for independent geometry only, preserving the source body identity in the derived model and checking analytic volume and area                                                          |
| `MakeCircleFeat` / `AddCircDimMut`    | Existing generative circle and radial graph. A primitive lowering needs an explicitly derived sketch and fixed centre.                        |
| `MakeBlindMut`                        | Existing depth and end graph. Lowering supplies the source `Height` in metres at the boundary.                                                                                                  |
| `ProjectCircle` / `ReadCircParams`    | Admits an explicit sketch and extrusion, the `D1` name, empty parameter attributes and two or three parameters. Primitive admission needs all thirteen owners. |
| `CheckCircMode`                       | Publicly admitted circle profiles do not include Front Plane, radius-driven, forward blind. Native companion authoring alone does not promote this profile                                    |
| `LowerBoxModel`                       | Requires an actual source `XY-plane`. This standalone cylinder has no source support datum.                              |
| `MakeAnchorNamed`                     | Complete named-body route is rectangle-guarded. A source circle body caption needs a separately qualified composition through the shared atom/name helpers                                    |
| Native metadata/property constructors | Existing vocabulary for the still-open FreeCAD metadata, attachment, material reference and additional parameter mappings                  |

A future source-specific preparation API should accept the actual `CadDocument`, an independently checked source-intent envelope, target policy and creation event, and return the shared `PartCandidate`. It must retain the original source separately from explicitly derived native support/sketch history. The source radius and height IDs must bind to the real native radial and depth owners, including their different native ownership locations. Renaming both parameters to `D1` in a stripped surrogate is not preservation of their actual source names and metadata.

No new serializer is needed for the already modeled circle, blind end, parameter, display, header or container owners. The unfinished work is source admission, complete semantic mapping and measured qualification of that composition.

## Reproduction and evidence limits

[`CheckCylinderAdmission.py`](../../tooling/sw2026/freecad_cylinder/CheckCylinderAdmission.py) takes a pinned SDK source root, the disclosed source directory, published source deck, published native-source receipt and a new output directory. Supply the exact SDK code manifest and its SHA-256. The two admitted inputs are `CylinderA` and `CylinderB`. It locks the requests and independent predictions before reading the native observation receipt. Both original FCStd and historical neutral hashes are checked again afterward.

The worker accepts a complete serialized `CadDocument` on stdin. The normal-read member accepts the original FCStd bytes on stdin. After the document is loaded, file reads are denied except imports from the hash-bound SDK source root. Runtime process and network calls are denied. Current source JSON copies stay private and are not generated native output.

The mutation cohort exercises missing/reordered drivers, stale values, foreign owners, changed units, labels, stripped or copied metadata, missing provenance, translated placement, partial sweep, active attachment, suppression, missing shape payload, changed source B-rep radius or height, an added formula and changed synthesized body naming. Every case fails before native emission.

The fifty observation comparisons reuse the [native source companion receipt](../measurements/2026/FreecadCylinderNativeSources01.json). They provide no new vendor execution, generated-file loadability, source equivalence, original held-out credit or public writer qualification. The next native dependency is independently locked source references before lowering, followed by a controlled generated-output trial with exact names, both independent driver edits and persistence.

Related evidence: [original source deck](FreecadOriginCylinderSources2026.md), [source ownership gotcha](../../../Documentation/Gotchas/Conversion/Freecad/Primitives/CylinderPrimitiveIsNotATwoParameterSketch.md), [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
