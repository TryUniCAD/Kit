# Disclosed native oblique-cylinder source authoring

Task `B04-SW2026-FREECAD-CYLINDER`; owner `/root/assembly_occurrence`; delivery PR #121. This tranche prepares an executable vendor source-author workflow. Root alone operates the Windows oracle. It implements no Kit CAD writer and does not qualify native generated or held-out conversion. The exit remains complete source-preserving primitive lowering with all CAD criteria, original source locks and measured generated acceptance.

The author follows the [exact public plane API binding](FreecadCylinderAngleApi2026.md), [angular plane ownership](FreecadCylinderAngledPlanes2026.md), [persistent selected direction](FreecadCylinderDirectionWire2026.md) and [selected-end lifecycle](FreecadCylinderSelectedEnd2026.md). [Host boundary receipt](../measurements/2026/FreecadObliqueCylinderAuthoring01.json) · [Later sealed protocol preregistration](FreecadObliqueCylinderSealedProtocol2026.json) · [Length-owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ReferencePlanes/ObliqueCylinderLengthIsTheLimitPlaneDriver.md)

## Explicit disclosed inputs

Both cases are independently authored full-circle local-Front profiles, centered at the local origin. They use positive vertical height, no thin walls, no draft, one extrusion direction and an actual selected height-limit plane. Angles below are radians; radius and height are metres. They are disclosed source experiments and must never be relabeled held-out.

| Case                  |  Radius |  Height | Tilt A |  Tilt B | Edited radius | Edited height | Edited A | Edited B |
| --------------------- | ------: | ------: | -----: | ------: | ------------: | ------------: | -------: | -------: |
| D01, `ObliqueCircleA` | 0.00743 | 0.02371 | 0.2173 |  0.4879 |       0.00917 |       0.03143 |   0.3497 |   0.2981 |
| D02, `ObliqueCircleB` | 0.01027 | 0.03619 | 0.3911 | -0.1637 |       0.00869 |       0.02837 |   0.2719 |  -0.3193 |

Each case has five immutable analytic states: original, after tilt A, after tilt B, after radius and after height. The author measures every step, so volume alone cannot hide a wrong tilt. It preserves the full actual native tree across edits and fresh original/edited reopens.

## Actual feature chain and call flags

1. Create `TiltHingeA` from actual Front and Right principal planes with `IModelDoc2.InsertAxis2(True)`. Create `TiltHingeB` from actual Front and Top planes. Both selected plane marks are zero for each two-plane axis. Capture actual endpoints as two point triples, then derive the line direction from their difference.
2. Select actual Right Plane with mark `0` and actual `TiltHingeA` with mark `1`. Call `IFeatureManager.InsertRefPlane(16 | optional 256, abs(tiltA), 4, 0.0, 0, 0.0)` and retain the one actual new `TiltPlaneA` feature.
3. Select actual Top Plane with mark `0` and actual `TiltHingeB` with mark `1`. Use the same call for `TiltPlaneB` and tilt B. Negative source tilt uses a positive scalar plus flip bit `256`; a negative raw scalar is not passed.
4. Construct actual `CylinderDirection` as the intersection axis of the two angular plane features, again through `InsertAxis2(True)` and two selected mark-zero planes.
5. Select actual Front Plane, mark `0`, and call `InsertRefPlane(8, height, 0, 0.0, 0, 0.0)` to create `HeightLimit`.
6. Author actual `CylinderSketch` on Front Plane. Create one non-construction `CreateCircleByRadius(0,0,0,radius)`, fix its actual center point through relation `17`, and create a real driving radial dimension with `AddRadialDimension2`. Retain the actual entity and native parameter ownership.
7. Select actual profile mark `0`, actual `HeightLimit` mark `1`, and actual `CylinderDirection` mark `16`. Invoke the exact 23-argument `FeatureExtrusion3` shape:

```text
True, False, False, 4, 0, height, 0.0,
False, False, False, False, 0.0, 0.0,
False, False, False, False, True, True, True,
0, 0.0, False
```

The positive distance argument is authored from height, but selected end `4` terminates on the real height plane. The editable physical length is `D1@HeightLimit`; no accepted blind boss-depth driver is inferred from the unused scalar. `Merge`, `UseFeatScope` and `UseAutoSelect` are explicitly true for this one-body boss creation. This does not prove selected-body or continuous automatic scope semantics for other operations.

The exact native route supports the selected plane/surface owner for type `4`. Public enum `10` remains outside this packet; there is no automatic substitution or invented type10 translation. Actual direction getter count must be one and its reference must be a real axis. The actual selected end getter must return a plane, whose complete transform is compared to the real owned height plane.

## Native preflight and observation

Metadata runs before CAD. It reads both registered libraries `34.0`, validates the six ordered plane arguments, all 23 extrusion arguments, the one `InsertAxis2(AutoSize)` argument, the actual `IPartDoc.FeatureByName` owner, angular/radial/linear enum names and the selected-end declarations. It records generated Python parameter signatures for the direction and end-reference getters without volatile default representations. A missing or mismatched prerequisite produces `MetadataFailure.json` with zero native launches.

The metadata preflight checks actual registered names. Historical primary API documentation supplies supplemental context only: [axis insertion](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDoc2~InsertAxis2.html), [axis endpoint array](https://help.solidworks.com/2024/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IRefAxis~GetRefAxisParams.html), [plane transform with respect to world](https://help.solidworks.com/2025/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IRefPlane~Transform.html) and [direction reference outputs](https://help.solidworks.com/2022/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IExtrudeFeatureData2~GetDirectionReference.html). These are earlier API editions; exact-build binaries and actual registered metadata govern this packet.

Each source has five serial fresh native processes: healthy control before, author plus four live edits and both saves, original reopen, edited reopen, healthy control after. Both source locks require all five identities to be distinct, time-ordered and healthy. Combined summary independently requires ten distinct identities across both cases. Each phase has its own immutable progress directory and raw record. A failed author does not prevent root from running its trailing control separately.

Actual angle and height definitions retain their constraints, selected-reference presence, values, public type and type2. Actual dimensions are bound freshly from their own feature display list to `D1@TiltPlaneA`, `D1@TiltPlaneB`, `D1@CylinderSketch` and `D1@HeightLimit`, checking physical dimension kind, driving/editable state, owner-qualified name and display value. No document-wide first-display shortcut is used.

Every live edit uses `SetSystemValue3(value,1,null)` and a fresh rebuild. The observer verifies one real solid, volume, area, center of mass, actual line/plane geometry, actual selected extrusion references, clean warning/error state and the full tree. It records all actual parent rows; the profile parent is mandatory and the separately queried end/direction owners establish their actual geometry. Original and edited source file digests are checked after closing and after each read-only reopen. Both native saves require `[true,0,0]`. Edited STEP and Parasolid text siblings are source geometry evidence, never writer inputs.

## Independent geometry and unresolved native edges

For signed tilts `a,b`, radius `r` and vertical height `H`, displacement is `(H*tan(a),H*tan(b),H)`, volume `pi*r^2*H` and center of mass half that displacement. The source prediction parameterizes the whole circular extrusion and computes area as two circular caps plus the lateral integral, using a fixed 4096-interval composite Simpson rule. Every expected state is frozen before native access in `Predictions.json`. Native observations never update those values.

Target normal predictions are `(cos(a),0,-sin(a))` and `(0,cos(b),-sin(b))`. Actual plane normals are compared as undirected plane normals with the correct plane position; the actual intersection axis must lie on the predicted line through origin. Native hinge orientation, positive angular rotation sign and COM tuple return representations remain unmeasured before this first batch. A mismatch fails and retains the actual raw observation. The observer does not flip, refit or select a favorable prediction afterward.

This first source packet excludes zero/obtuse/multiple angular planes, partial sectors, arbitrary Placement, attachment systems, arbitrary existing plane/sketch sources, noncircular profiles, multiple bodies and selected-end type10. These are unfinished goal requirements, not omitted source semantics inside an accepted conversion. Full FreeCAD thirteen-property preservation and generated writer acceptance remain separate obligations.

## Reproducibility and custody

`ObliqueCylinderSources.py prepare` freezes four new source tools plus nine existing checked-in helpers into a new private `Tools` directory. It binds the actual disclosed healthy control SHA, prior API manifest, exact neutral cases, independent predictions and every tool hash in `Protocol.json`. `verify` and `metadata` run separately. The private `Recipe.json` contains exact explicit interpreter argv and uses canonical Windows paths; root alone transports them with the reserved VM protocol.

The host receipt records the real freezer/verification boundary: two fresh successful verification processes and five refusals covering packet hash, tool/input mutation, hidden slot and host native execution. AST/compile and formatting are static checks. No COM object, CAD process, hidden file or Hopper target was accessed by preparation. The source packet contains a disclosed vendor control solely for the oracle; no vendor executable, raw listing or captured field program is part of the source tranche.

The later sealed-source protocol is preregistered independently and disabled. This packet has no hidden slot argument and refuses an altered disclosed model even if its manifest is rehashed. No hidden native design or neutral bytes were materialized, read or generated on the host. Native acceptance and all source locks remain pending until root executes the pinned recipe and verifies the actual outcomes.
