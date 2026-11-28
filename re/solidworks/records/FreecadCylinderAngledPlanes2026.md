# Editable angular planes for the five-driver cylinder

Task `B04-SW2026-FREECAD-CYLINDER`; owner `/root/assembly_occurrence`; delivery PR #121. This is exact-build construction and archive knowledge, not a new writer or native acceptance. Dependencies are the [five-driver lowering](FreecadCylinderFiveDriverLowering2026.md), [persistent direction graph](FreecadCylinderDirectionWire2026.md), [selected-end lifecycle](FreecadCylinderSelectedEnd2026.md) and existing [reference-plane construction](ReferencePlaneManagedConstruction2026.md). Exit remains a complete source-preserving primitive with independently locked native open/edit/rebuild/save/reopen acceptance. Both earlier frozen packets are preserved.

The angular plane's scalar constructor is not its completed editable state. The actual plane feature must own its data before initialization creates the angular display, dimension, handle and parameter graph. Two distinct current construction paths exist; a public API type or a C++ base name cannot select the wire tag by itself. [Numeric source record](FreecadCylinderAngledPlanes2026.json) · [Reproducible receipt](../measurements/2026/FreecadCylinderAngledPlanes01.json) · [Initialization gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ReferencePlanes/AngledPlaneInitializationOwnsItsDriver.md)

## Exact inputs and evidence boundary

| Original module | SHA-256                                                            | Preferred base |      Bytes |
| --------------- | ------------------------------------------------------------------ | -------------- | ---------: |
| `sldmodu.dll`   | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | `0x4b140000`   | 46,536,280 |
| `sldcoreu.dll`  | `3af88769b06bf7a1510fe52f279fbda20e5dc5548dc3925a1357e0f71cc3b3e3` | `0x180000000`  |  5,416,536 |

The mixed core MVID is `3f9c2ded-9024-4b12-ac82-deb36cae1451`, CLI flags `0x18`. CIL methods are parsed as CIL. Native import thunks are resolved through their actual IAT and the complete original model export table; native bodies are never decoded as managed IL. All addresses below belong to these module identities. Scope is document version `19000`, SOLIDWORKS `34.5.2.0604`.

The replay pins 31 CIL methods, 42 complete native functions, 11 runtime descriptors, 7 managed/native boundaries, 25 call edges and 27 virtual slots. Chained unwind fragments are grouped with their primary function, including all three parts of the angular quadrant setter and interface serializer. Only numeric identities, call metadata and independently written field rules are distributed. Private vendor instruction/IL listings remain outside the delivery.

## Actual constrained inputs and compatibility fork

`LnPlNullPlaneEvaluator_c.isCoincLineAtAnglePlane` (`0x06004f27`, RVA `0x139160`) requires an actual `CoincidentGeom_c` line and an actual `AngleGeom_c` plane. The parallel and nonparallel tests (`0x06004f25/26`) refer to the selected line relative to the selected plane, not to the requested angular value. Three-geometry creation (`0x06004e15`, RVA `0x136368`) retains input slots `0,1,2`, with null for each absent input. Do not sort selected references by class or ID.

| Construction edge                                                | Concrete result                                                                                                                                                                      |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `createRefPlaneDataNewType`, `0x06004f29`, RVA `0x139c58`        | After its separate perpendicular/projection cases, the ordinary angled case and the parallel case without the old/API guard select `moConstraintCoincLineAtAnglePlaneRefplaneData_c` |
| Concrete allocator, `0x06004f2b`, RVA `0x139198`                 | Allocates `0x158` bytes; calls model `0x4b8dfe00`; explicitly publishes common type `f5c=22`                                                                                         |
| `createRefPlaneDataPacket`, `0x06004f32`, RVA `0x139ee8`         | A parallel case with `isOldRefPlaneOrCreatedByApi` takes the compatibility `Angle_c` route, except the separately checked existing cone-normal case                                  |
| `convertToAngle`, `0x06004f33`, RVA `0x139328`                   | Keeps the actual plane and line, requested angle and reverse; passes projection-line mode zero; sets both original input reference indexes independently                             |
| Compatibility `Angle_c.CreateData`, `0x06004d05`, RVA `0x13237c` | Allocates `0xb8` bytes; clones the actual plane and line wrappers; calls model `0x4c2da960`; publishes `f5c=7`; applies both actual indexes through virtual setters                  |

The old/API guard is the already mapped unsigned create-version `<4150` test plus the actual plane-data old-API predicate. It is a construction fork, not a 2025-to-2026 wire difference. The new-type factory has additional default/projection paths. This record does not collapse them into the concrete coincident-line/angle-plane member.

`AngleGeom_c.CreateData` (`0x06004c73`, RVA `0x12ec70`) allocates `0x48` bytes and calls `moRefPlaneAngleGeom_c(actualWrapperClone, angle, reverse)` at `0x4c2d77a0`. The managed count is separate: its setter can constrain a multiple-plane request and its angle setter uses `6.2831853071796`. No extra count field is serialized in the angle-geometry suffix. The proposed ordinary single-plane input must declare count one; this is not authority to discard a multi-plane request.

## Runtime class publication and current wire

| Actual class                                      | Object size | Runtime descriptor | Vtable       | Serializer   | Archive schema |
| ------------------------------------------------- | ----------: | ------------------ | ------------ | ------------ | -------------: |
| `moConstraintCoincLineAtAnglePlaneRefplaneData_c` |     `0x158` | `0x4dad2580`       | `0x4ced1c20` | `0x4b8e2a30` |              1 |
| `moRefAtAngleData_c`                              |      `0xb8` | `0x4daf31f0`       | `0x4d137f30` | `0x4c2754a0` |              1 |
| `moRefPlaneAngleGeom_c`                           |      `0x48` | `0x4daf67f8`       | `0x4d173b10` | `0x4c2d8a40` |              1 |
| `moRefPlaneCoincidentGeom_c`                      |      `0x38` | `0x4daf6798`       | `0x4d1739d0` | `0x4c2d8ad0` |              1 |
| `moConstraintRefplaneInterfaceData_c`             |      `0xa8` | `0x4dad2340`       | `0x4cecfbc0` | `0x4b8e2b70` |              1 |

The intermediate base-angle vtable `0x4ced19d0` has the larger angle serializer at slot 5 but publishes **`moConstraintRefplaneData_c`**, descriptor `0x4dad2370`, through slot zero `0x4b8df460`. The concrete coincident-line subclass overrides slot zero with `0x4b8e27e0` and its own `0x158` class. An abstract/base angle name is not a standalone archive-construction recipe. This mirrors the independently recorded [publication distinction](ReferencePlaneRuntimePublication2026.md).

The common constrained serializer (`0x4b8e2ac0`) runs current plane-data serialization and writes actual interface object `f88`. The interface serializer writes exactly three geometry objects at `f08/f10/f18`; loading a nonnull incompatible class throws. Each geometry base (`0x4c2d8b90`) owns its selected wrapper `f08`, two scalar selection coordinates and helper point `f20`. `ConstrainedGeom_c.Apply` (`0x06004c43`) uses an authored helper point when present, otherwise its near point. A blanket zero helper/projection rule has not been established.

The angle geometry adds `f64 f38` and one boolean byte `f40`. Loading converts exactly byte `1` to true. The base-angle data serializer (`0x4b8e2930`) adds `i32 f148` followed by actual angular-display object `f150`; load rebinds that display to the real plane and prepares adornments. The concrete coincident-line serializer adds no stored field; its load path sets runtime `fe8=1`.

The modern compatibility serializer (`0x4c2754a0`) writes, after common plane data, embedded plane wrapper `f90`, actual line object `f98`, angular-display object `fa0`, then `i32 fa8/fac/fb0/fb4`. These are flip, projection-line mode and the two actual input reference indexes. It does **not** separately store scalar runtime `f88`. Legacy line representation changes at `0x169`; projection mode is read at `>=0x10a7`, and explicit reference indexes at `>=0x10d5`. Version `19000` takes the modern branches. Older loader defaults do not authorize reordering a new input.

## The editable driver is created by initialization

`ConstrRefPlaneDataPacket_c.CreateFeature` (`0x06004c03`, RVA `0x1312cc`) validates, creates data, rejects a null result and constructs the actual `moRefPlane_c` when needed. It sets data `f10` to that plane, calls `moRefPlnData_c.init(1)` and publishes the plane into the request feature list. Model init `0x4c2f25d0` dispatches actual virtual `+0xa0`.

| Actual init                | Published angular owner                                                                                                                                                                                                                             |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Constrained `0x4b8ed160`   | Prepares geometry, obtains the actual angle, allocates `0x1020`, selects `AngleDim_c`, supplies null explicit model, real plane owner, dimension role `1`, final constructor flag `1`, calls `moDisplayAngularDim_c` at `0x4c85a8d0`, stores `f150` |
| Compatibility `0x4c2f1530` | Uses runtime scalar `f88` with the same class, role, owner and constructor flag, stores `fa0`; the earlier scalar constructor initialized this pointer null                                                                                         |

With the nonzero init flag these paths also perform actual plane update and status/placement work. The shared display constructor `0x4c86f550` creates the real `AngleDim_c` through `0x4c820d30` and one retaining `moFeatureDimHandle_c`. Angle-dimension virtual `+0x3d8` selects `0x4c821470`, which creates `moAngleParameter_c`. The actual graph is therefore `plane → display → feature handle → AngleDim_c → moAngleParameter_c`, with owner aliases back to the same plane. Role `1` feeds the shared naming path; exact final label, header allocation and native edit behavior still require this family's source controls.

Angular display text kind is `13` at virtual `+0xae0 → 0x4b2fd760`. Existing [shared dimensional constructors](ProfileConstruction2026.md) are relevant to that subgraph, but their production `RequireDisplay` guard currently excludes `moRefPlane_c`. This investigation does not widen it. The zero-draft display's measured placement is not evidence for a nonzero-angle plane's final placement/style.

Constrained `setAngleDim` (`0x4b8f7dd0`) releases old `f150`, clears it, updates the actual angle-geometry scalar through virtual `+0x230 → 0x4b8f7d60`, then calls init with flag zero. Compatibility setter `0x4c2f6210` releases old `fa0`, updates runtime `f88` and invokes its actual init with flag zero. A null display at that intermediate point is not a completed editable feature. Managed readback `0x06004da8` follows actual display virtual `+0x868`, not a guessed scalar cache.

## The constrained selector is derived, not a copied default

Base construction starts `f148=0`. Reference-frame preparation `0x4b8e73a0` chooses a new selector when zero or when its geometric incompatibility predicate at `0x4b8f2e10` returns nonzero. That predicate reconstructs a basis and tests whether the selected line direction is perpendicular to it. It is not a generic true-means-valid validator: zero or absolute values greater than four return zero without a successful geometric result, so the caller does not promise to repair an arbitrary invalid nonzero selector.

Chooser `0x4b8e31c0` gets the selected plane normal `n` and actual line direction `l`. When they are not perpendicular, it chooses signed `4`, with sign from `n·l`. When they are perpendicular, it copies **the line direction**, then transforms that vector through the inverse of the selected line wrapper's actual frame (`calculateXform`, then inverse, then unit-vector transformation). The actual imported `mgUnitVector_c` copy constructor at call `0x4b8e3354` binds this operand. Picker `0x4b8e3150` selects the signed dominant local coordinate: Y replaces X only if `abs(y)>abs(x)+1e-10`; Z replaces the current coordinate only if `abs(z)>current+1e-10`. The result is `±1/±2/±3`. Ties retain the earlier axis. The `1e-10` comes from original constant address `0x4cd9a3a8`.

Companion basis helper `0x4b8e8700` reconstructs signed local X/Y/Z for `±1/±2/±3`. Helper `0x4b8e8a70` uses the selected plane normal for `±4`. This explains the incompatibility predicate: the basis should not be perpendicular to the actual line. An initial private interpretation that the inverse-frame operand was the plane normal was refuted by the copy-constructor operand and companion helpers before the delivery froze; no constructor or native output used it.

Thus `f148` is neither an angle nor a universal axis ID, and zero is only constructor staging. The exact relative frame and selected geometry determine it. Current native source correlation is still required before a new writer emits the completed graph.

## Concrete next construction and remaining gates

Retain the prior analytic proposal: `nA=(cos(a),0,-sin(a))`, `nB=(0,cos(b),-sin(b))`, giving intersection direction proportional to `(tan(a),tan(b),1)`. Keep both angle planes independent, select a real line/axis lying in each base plane, and bind each real angular parameter to its corresponding source tilt. Build the actual intersection-axis graph from those two plane features, and use that selected axis and the actual height-offset plane in the already mapped end/direction owners. Apply the source rigid Placement to the whole chain.

The construction scaffold now has explicit owners:

1. Retain the source local frame and three actual support datums, transformed together by source Placement. Derive any lowering-only datum names and IDs in a separate source-to-target ownership map.
2. Supply two real line references for the angular planes. Local +Y and -X are the analytic rotation axes; if constructed as principal-plane intersections, retain their actual ordered plane references and measure the resulting direction sign rather than assuming it from their names.
3. Pair each actual line `CoincidentGeom_c` with its actual selected plane `AngleGeom_c`, retaining the input triplet indexes, angle/reverse inputs and any required selection coordinates/helper point.
4. Select the real concrete/compatibility publication route from the measured construction method. Create the actual plane, bind its data owner, complete the role-one angular display graph and allocate its identifiers through the shared model header.
5. Derive the constrained reference-basis selector where that route uses one. Preserve native geometric validity, signed angles and the actual wrapper frame. Do not write constructor zero as a finished selector.
6. Build the final intersection axis from those two actual planes, then reference it from the extrusion direction and reference the independently offset height plane from the selected end. The earlier packets supply that persistent graph and identify its separate display lifecycle.

These steps are a source-grounded design. They do not supply unmeasured final plane transforms, dimension placement, sign normalization or a qualified zero-angle publication. In particular, reversing one actual axis reference may require a different angular input/reverse flag while representing the same analytic normal. Only the independent native source cohort can bind that convention.

The analytic orientation alone does not choose native reference order, reverse flag or signed angular convention. The native author protocol must measure those, including zero and mixed signs, the actual compatibility/constrained archive owner, both real angular dimensions, selected reference identity, resulting plane/axis frames and live edits through save/reopen. Lock independent held-out native sources before writer code. Existing offset, radial and selected-end source coverage does not substitute for these locks. Full/partial sweep transition and complete FreeCAD metadata/attachment preservation remain separate requirements.

The current shared angle-plane schema/constructor boundary is incomplete; this delivery adds no archive writer, source admission, native candidate or fallback. It provides the pinned construction route and exact conditional owner obligations needed for the next source cohort. All semantic fields retain `partial` confidence under the playbook because native source correlation, boundary probes and generated acceptance are absent.

## Replay

```sh
uv run --no-project --offline --isolated --python 3.11 \
  --with dnfile==0.18.0 --with dncil==1.0.2 --with pefile==2024.8.26 \
  python -B re/tooling/sw2026/freecad_cylinder/PinCylinderAngledPlanes.py \
  --root /absolute/Kit \
  --inputs /absolute/licensed-originals \
  --knowledge re/solidworks/records/FreecadCylinderAngledPlanes2026.json \
  --output /unused/AngledPlanePin.json
```

The output file must be new. The tool validates original module hashes, MVID, CIL/native distinction, expected whole-function identities, descriptor publication, source allocation/mode arguments, actual init and reference-index edges, virtual slots and numerical constants. It writes numeric research evidence only. Two independent exact-input replays must agree, and wrong module/version inputs must fail without producing a receipt. The adjacent measurement receipt records those actual outcomes and both previous frozen-packet preservation checks. No CAD runtime or model file is needed.
