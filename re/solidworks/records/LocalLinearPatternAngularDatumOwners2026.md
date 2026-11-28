# Constrained angular datum ownership in SOLIDWORKS 2026

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121. The ordinary Top/Right hinge and its angled datum have a complete typed Config-0 and ResolvedFeatures replay on four disclosed native saves. The saved plane's editable D1 and selected Right plane, finite hinge, angular display and defined annotation view remain joined. The analytic prediction also derives the datum frame, presentation and representative angular adornments from the separately authored stock and angle. [Bound measurements and tool hashes](../measurements/2026/LocalLinearPatternAngularDatumOwners01.json) · [Earlier finite hinge model](LocalLinearPatternHingeAxisGraph2026.md)

## Archive and role checks

The local research grammar extends the existing SDK axis, feature, dimensions and reference field primitives. It uses the actual version-19000 `moRefPlane_c` with `moConstraintCoincLineAtAnglePlaneRefplaneData_c` at `f6f8`. Its `f88` interface keeps the following order.

| Slot | Required typed role |
| --- | --- |
| `f08` | Actual `moRefPlaneAngleGeom_c`. Its `moPlaneRef_w → moCompRefPlane_c` selects the same registered Right plane as the hinge's second plane. `f38` holds the positive authored radians and `f40=0` the unreversed constraint. |
| `f10` | Actual `moRefPlaneCoincidentGeom_c`. Its `moLineRef_w → moCompRefAxis_c` selects the registered finite through-origin hinge. The line carries the first endpoint, negative-Z direction and finite span. |
| `f18` | A separate `moRefPlaneCoincidentGeom_c` exists. Its wrapper is null. The three geometry rows have the midpoint pick coordinates and origin helper state from `moRefPlaneGeometry_c` construction. |

The Right, hinge and two hinge-plane references use separate local component vertices in the same actual Config-0 model. Each registered target ID is paired with its corresponding creation log from both part headers. The constrained subtype uses `f5c=22`. The unedited and spacing-edited saves retain `f54=f58=-4` and `f148=-3`, consistent with the current ordinary constructor markers and the signed negative-Z selector of the selected straight line. [Role checks](../../tooling/sw2026/linear_pattern/CheckPatternAngleOwners.py) · [Constraint construction and selector source](FreecadCylinderAngledPlanes2026.md) · [Local typed wire](../../tooling/sw2026/linear_pattern/PatternAngleWire.py)

The actual angular display is `f150 → moDisplayAngularDim_c.f850[0] → moFeatureDimHandle_c.ff0 → AngleDim_c.f28 → moAngleParameter_c`. The display owns exactly one handle, with no external dimension reference. The parameter name is `D1`, and its radians independently agree with the typed input angle and the one-element display descriptor. The display's arc marker `f100c=1` is written by the live adornment path. The persistent dimension ID and the display cache are distinct from the constraint angle. The current exact-build load branch rebinds the angular display to the actual plane at `0x4b8e29aa`.

## Derived shape and adornment

The checked model uses the canonical Right normal `+X` and the ordered finite hinge's `-Z` direction. The normal follows the positive, unreversed rotation around that line. The in-plane frame uses the hinge direction first and `normal × hinge` second. The pinned routine at `0x4b8ee700` projects the reference-plane normal to the hinge's perpendicular plane before transforming it. Existing border logic supplies the ordered padded square from the actual finite endpoints. The resulting four corners define the display centre and the second corner rule for the name position. [Finite border rule and point order](LocalLinearPatternDatumBorders2026.md) · [Independent geometry calculations](../../tooling/sw2026/linear_pattern/PatternAngleGeometry.py)

The exact ordinary adornment routine `[0x4b8f4fa0,0x4b8f5986)` uses the actual display handle and the constrained plane's display centre `C`. For the unreversed local shape, the first ray follows the selected Right plane's positive Y tangent. The second follows that tangent rotated around the hinge by D1. The two witness points are `C + 1 mm × ray` and the third point is `C`. The live dimension plane has local `(-X,+Y,-Z)` axes and inverse translation `(-dot(C,Xlocal),-dot(C,Ylocal),-dot(C,Zlocal))`. The initial label calculation forms the midpoint of the two witnesses, normalizes its in-plane displacement from `C`, then adds the resulting offset at the hinge. It uses the initial `f8b0` getter for radius and a 1 mm fallback when that radius is near zero. The measured label direction and length match the projected displacement in the dimension plane. The stored chord length `fad0` matches the distance between the two witnesses.

The four complete source stream pairs and maps replay exactly. Each includes 24 roots and the MBSM trailer. Config starts ResolvedFeatures at `112`; each replay reaches `472`. The four ResolvedFeatures sizes are 33618, 33860, 33618 and 33618 bytes. The geometry compares to independent authored inputs, with exact four border values per file and a maximum witness point error of `1.734723475976807e-18` m over 12 points. The maximum label-direction difference is `3.510833468576701e-16`. These tolerances apply to the geometry proof. The source re-emit is byte-exact. Four in-memory probes per disclosed graph reject a camera ID in the annotation field, a crossed constraint row, an absent third geometry and a different live driver.

Two additional analytic inputs use different stock and independent angles of 28.625° and 63.125°. Four fresh guarded computations consume only neutral stdin and record zero runtime file reads. Their independent closed forms check witness centres and chord lengths. They produce no CAD files. The four saved native angles in this cohort are 45°. The two additional angles are host-only predictions.

## Cross-stream annotation owner

`moDisplayItem_c::addViewId` at `0x4ba678e0` records membership at `f2b0`. Its `getAnnotationView` at `0x4ba69760` obtains the saved view ID and resolves it through the actual owning model's `getViewWithThisId`. The part stores a separate `moAnnotationView_c` collection at `fa48`; ordinary camera views are at `f9f8`. `moModel_c::addAnnotationView` at `0x4c015440` appends to that actual annotation list. Every disclosed oblique D1 selects `*Back` at annotation ID 201. The ordinary `*Back` camera ID is 2 and has a distinct stored presentation transform. The real `*Back` annotation orientation agrees with the dimension frame.

The annotation catalogs also vary independently of the number. The two disclosed principal parts have annotation ID 201 for `*Front` and `*Left` respectively. Their ordered names are `*Top, *Front` and `*Top, *Left, *Front`. The oblique row order is `*Top, *Back`. `feb0` equals the highest actual annotation ID in all six models and `feb4=199` is independently unchanged. The current ordinary part constructor creates an empty annotation collection and seeds both counters to 199. The generative prerequisite is actual annotation-view construction and membership from represented model intent. The native initial allocation and display-frame inputs must preserve separate annotation and camera transforms and the shown-view state. Arc-engine leaves beyond the checked witness, label direction, radius and chord need their own derived or proven cold-state rules. This work leaves those construction paths, the complete generated angular graph and all native/public/pattern writer acceptance pending. [Annotation join gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Patterns/AngleDisplayUsesAnnotationViewIdentity.md)

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternAngleOwners.py \
  --binaries /absolute/licensed/module/directory \
  --disclosed-share /absolute/share/Oracle121Takeover \
  --output "$(mktemp -d)/ConstrainedAngleOwners.json"
```

Use the exact independently pinned module and source files. All disclosed readings are in the outer verifier. The isolated model processes need no saved data, CAD application or protected input.
