# Source-preserving cylinder lowering: five geometric drivers

Primitive lowering remains unfinished. This is a source-bound design and static trace, with zero generated native files, CAD processes, sealed inputs or shared-source changes. It does not qualify an oblique writer.

Task `B04-SW2026-FREECAD-CYLINDER`; owner `/root/assembly_occurrence`; delivery PR #121. Root owns integration and the oracle. Dependencies are the [five-driver source semantics](FreecadCylinderPropertySemantics2026.md), existing SDK part/datum models and pinned SOLIDWORKS `34.5.2.0604`. Exit remains complete source preservation with live edits and independently locked native acceptance. [Exact evidence and source hashes](FreecadCylinderFiveDriverLowering2026.json)

## What must be represented

In the primitive's local frame, let `r`, `H`, `theta`, `a`, `b` be `Radius`, `Height`, `Angle`, `FirstAngle`, `SecondAngle`. The exact FreeCAD source constructs a circular/sector base in local XY, then translates it by

`d = (H tan(a), H tan(b), H)`

with angles converted from degrees. Source Placement applies to that entire construction afterward. Radius and height alone reproduce only the current ordinary geometry. Dropping the other live inputs does not preserve the primitive.

| Source owner  | Candidate native owner                                                                     |
| ------------- | ------------------------------------------------------------------------------------------ |
| `Radius`      | Radius-driven circular/sector profile dimension                                            |
| `Angle`       | Live sector-sweep owner, with an explicitly qualified full-turn/partial-turn transition    |
| `FirstAngle`  | First direction-control plane's angular dimension, or an equivalent live equation input    |
| `SecondAngle` | Second direction-control plane's angular dimension, or an equivalent live equation input   |
| `Height`      | A limit-plane offset along the original local Z, or a live input to a derived blind length |

Generated support/history features must be identified as lowering-derived. Retain source IDs and a declared source-to-target ownership map; do not falsely attribute the generated sketch, axis or datums to the FCStd document. The other eight scalars, six nonscalar owners, naming, materials and metadata remain obligations from the complete envelope.

## A datum route avoids trigonometric target equations

Keep the base profile in the original XY plane. Construct two origin planes with normals

`nA = (cos(a), 0, -sin(a))`, `nB = (0, cos(b), -sin(b))`

The first rotates the YZ plane about local +Y by `a`; the second rotates the XZ plane about local -X by `b`. Their intersection direction is

`nA × nB = cos(a) cos(b) (tan(a), tan(b), 1)`

The source's open `(-90°,90°)` prism-angle domain makes the Z sign positive. A reference axis from that plane intersection, a height plane at local `z=H`, and an explicit-direction extrusion ending on that height plane reproduce `d`. This keeps `H` as a real vertical offset and places both tilt inputs on real angular datums. Apply the source rigid Placement to all frames, not only the boss.

This is an analytic lowering proposal, not measured native construction. A private independent mathematics probe passes 63 comparisons across seven disclosed synthetic angle/height combinations, including zero and mixed signs; maximum difference is `7.105427357601002e-15 mm`. No CAD geometry was generated. The axis is analytically well-defined at zero angles, but native zero-angle datum publication, signed angles, reference-axis ownership and selected-end lifecycle are still unmeasured.

## Compact blind alternative and the depth ambiguity

A generated direction line or two points can instead supply `u=d/|d|`, with blind length `L=|d|=H sqrt(1+tan(a)²+tan(b)²)` **if** the native blind metric is along that direction. This requires live relationships, not a precomputed vector and scalar. A literal vector loses the angle edits; copying `H` into an along-direction length changes vertical height.

The inspected 2026 [depth API](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IExtrudeFeatureData2~GetDepth.html) reports the selected end's depth. The exact native getter `0x4badf660` follows its display/handle and retrieves its value. Neither observation alone establishes the oblique distance metric. Measure one non-normal blind control's endpoint, API depth and actual driver before choosing `H` versus `L`; do not fit a formula to a cache. The datum/height-plane route avoids that blind metric dependency but adds selected-end construction work.

## What the SDK and exact native trace actually supply

| Existing boundary                     | Proven fact and remaining work                                                                                                                                                                                                                                                                        |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ExtrudeFeature.direction`            | A numeric spatial vector exists; it has no direction-reference identity or two live angle bindings                                                                                                                                                                                                    |
| `BoundDatum` / `GetDatumFrame`        | A typed angle or offset parameter can control a datum frame; angles here use radians. This neutral evaluator is not a SOLIDWORKS datum writer                                                                                                                                                         |
| `PlaneExtrude` / `GetPlaneRise`       | Selected-plane intent exists, but current evaluation requires the profile, limit and extrusion normals to be co-directed; it rejects this oblique member                                                                                                                                              |
| `ProjectCircle` / `ReadBossEnd`       | Admission requires canonical origin support and the actual support normal; non-normal direction rejects                                                                                                                                                                                               |
| `ReadCircParams` / `RequireExtrusion` | Requires the admitted unexpressed `D1`/`D2` drivers and simple selections; the thirteen-property primitive and source names are outside that profile                                                                                                                                                  |
| `MakeEndSpec`                         | Current constructors deliberately set explicit direction `f138` to null; changing a cached frame or the reversal flag cannot supply an owned direction graph                                                                                                                                          |
| Native `moEndSpec_c`                  | `getDirSpec` `0x4b283bd0` and `setDirSpec` `0x4b30fb20` directly access `f138`. The separate `f8c` direction integer is reversal, not a vector                                                                                                                                                        |
| Native `moDirectionSpec_c`            | Vector, single-reference and two-point constructor overloads exist; the current serializer is `0x4c695dd0`. The vector overload copies numeric geometry; reference paths allow dependency-bearing inputs. Their complete non-null graph and legal flags still require a controlled 2026 source corpus |

Native facts were independently read from original `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, using bounded stateless PE/LLVM inspection. The evidence pins eight native windows, constructors and resolved imports. No Hopper session was opened, and proprietary listings remain outside the checkout.

The existing [plane construction trace](ReferencePlaneConstruction2026.md) identifies the concrete angular dependency: `moConstraintAtAnglePlaneRefplaneData_c` adds selector `f148` and actual angular display `f150`, serialized at `0x4b8e2930`. A rotated cached frame is not a replacement for that owner. Its complete angle/axis/publication path remains separate from the qualified offset-plane constructor. The 2026 class map also identifies `moRefAxis_c`, but a class descriptor alone does not supply an intersection-axis writer.

The published [2026 direction-reference getter](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IExtrudeFeatureData2~GetDirectionReference.html) distinguishes one reference from two and reports actual entity types. The [2026 extrusion interface](https://help.solidworks.com/2026/english/SolidWorks/sldworks/r_extrude_propertymanager.htm?format=P) permits non-normal direction. These contracts support a source-authoring probe; they do not authenticate the local registered method signatures or a serializer mapping. The [2026 public end enum](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swEndConditions_e.html?id=db3cfc793dcc412a94c6e64da4c926a5) uses `swEndCondUpToSelection=10` and retires old surface/vertex selectors. Do not copy that API number into `moEndSpec_c.f0c` without the actual translation rule.

## Locks and next executable milestone

Existing circle, end-condition and offset-plane locks can support their unchanged radial/blind/offset subgraphs. They do not qualify an oblique direction owner, angled planes, intersection axis, selected-plane end, live primitive sweep or complete FCStd lowering. No suitable five-driver primitive lock was found in the inspected public lock inventory; no sealed payload, neutral specification or observation was opened.

The next milestone is a metadata-first native source cohort, before any new writer: separately vary each tilt, both tilts, angle sign, zero-angle state and full/partial sweep; include an independently defined non-normal blind metric control and the datum/axis/height-plane alternative. Record actual ordered references, live source-named drivers, endpoints, cap/base frames, geometry and edits through save/reopen with healthy brackets. Freeze unrelated hidden sources before construction code. The full-turn-to-partial profile transition is a separate hard gap: the current closed-circle graph has no equivalent sweep dimension, and two coincident radial sides cannot simply be assumed valid at 360°.
