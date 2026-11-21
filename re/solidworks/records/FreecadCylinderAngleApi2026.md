# Exact public API binding for editable angular planes

Task `B04-SW2026-FREECAD-CYLINDER`; owner `/root/assembly_occurrence`; delivery PR #121. This is a source-only continuation of the [five-driver lowering](FreecadCylinderFiveDriverLowering2026.md), [persistent direction](FreecadCylinderDirectionWire2026.md), [selected-end lifecycle](FreecadCylinderSelectedEnd2026.md) and [angular-plane construction](FreecadCylinderAngledPlanes2026.md). The exit condition remains complete source-preserving native history with independent held-out open, edit, rebuild, save and fresh reopen acceptance. No writer, source qualification or native acceptance is added here.

The public `InsertRefPlane` call now has an exact pinned route to the managed geometry triplet. Its constraint masks, selection marks and angular values no longer depend on a historical API example. [Numeric knowledge](FreecadCylinderAngleApi2026.json) · [Replay receipt](../measurements/2026/FreecadCylinderAngleApi01.json) · [Two-case source protocol](FreecadCylinderAngleAuthorProtocol2026.json) · [Selection and lifecycle gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ReferencePlanes/PlaneApiMarksAndAngleSigns.md)

## Inputs and evidence scope

All images are lawful original files retained outside the checkout. Addresses are preferred virtual addresses for the exact image, not relocated runtime addresses. No original module, native code listing, IL listing or saved CAD data belongs to this tranche.

| Image             |      Bytes | SHA-256                                                            | Additional identity                                                                |
| ----------------- | ---------: | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `sldapiu.dll`     | 19,441,752 | `97bc3d859637c8b420108a1a3ebd4262580fa45d05c761874df7658fad49b6c2` | Build `34.5.2.0604`, image base `0x423f0000`                                       |
| `apicoupleru.dll` |  1,396,312 | `de69e03b5818a91311af2488ec08bb21954a6c0b131138373e2014a0d4232eaf` | Build `34.5.2.0604`, MVID `149fe54a-217f-4a9a-a467-01838eff8420`, CLI flags `0x18` |

The numeric record also binds the exact `sldappu`, `slduiu`, `sldmfcu` and `sldcoreu` inputs and every reused evidence tool. The coupler is mixed native/C++/CLI, not an IL-only assembly. REA target-free artifact evidence `ev_23d9f791797c196d8a1188b8bac4df398a63d9de5d814f2573ff5aa8cfdd1df3` and selected-member evidence `ev_e6f9eaf53b43d1f935bb5faf9679c24272ce2bf6151789235fa0c211aea97544` independently bind its module and selected types. Decoded method tokens stay local to that SHA and MVID. No target code was loaded or executed.

The existing metadata-only native receipt SHA `fb37d7dcde62d33b33564fa4fddba6f9c37ffbf3f681e70bd0bd4925e917b010` supplies registered library `34.0`, `IFeatureManager` IID `{6B39655E-381B-4BD0-89F5-640D48593F15}`, `InsertRefPlane` DISPID `182`, argument types `I4,R8,I4,R8,I4,R8` and dispatch return. That earlier metadata is not a newly authored angular-plane source. All semantic rules below remain **partial** under the playbook until actual angular-plane sources and generated native acceptance corroborate them.

## Actual public owner and command

The app wrapper at `sldappu:0x45658f20` preserves all six arguments and invokes the actual feature-manager interface at vtable `+0x628`. The UI connection getter `slduiu:0x49784b60` obtains the real manager through `appApiBridge` virtual `+0x480`.

`appApiBridge::getBridge`, `sldappu:0x45843c60`, supplies stem `sldapi` to `SldMFCUtils::LibUtils::GetLibHandle`. Pinned `sldmfcu:0x3c84bde0 → 0x3c84bed0` appends `u` then `.dll`, and uses `GetModuleHandleW` before `LoadLibraryExW`. The exact filename is therefore `sldapiu.dll`. There is no dependency on a guessed literal `sldapi.dll` file.

| Binding                           | Pinned source                                                                                                                                                     |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Actual bridge factory             | `sldapiu` vtable `0x43219fe0`, slot `+0x480 → 0x42a98570`                                                                                                         |
| Real feature-manager construction | `0x42a98570 → 0x42c32a20`, `0x88`-byte allocation                                                                                                                 |
| COM interface ownership           | Constructor stores actual XDispatch vtable `0x432521e8` at object `+0x78`; methods subtract `0x78` to recover the actual owner                                    |
| `InsertRefPlane` interface slot   | `0x432521e8 + 0x628 → 0x42c66e80`                                                                                                                                 |
| Ordinary implementation           | `0x42c66e80 → 0x42c7c8f0`; requires `uiEnvironment::useWpfCommands`                                                                                               |
| Native command dispatch           | `apiCouplerLoader::createRunningCommand`, command `0x70`, library stem `apicoupler`                                                                               |
| Exact coupler filename            | Same suffix rule gives `apicoupleru.dll`                                                                                                                          |
| Registered factory                | `apicoupleru:0x18004fc30`, call `0x18004fdc9` registers `0x70 → 0x1800535d0`                                                                                      |
| Native-to-managed constructor     | Factory calls `0x18005e2a0`; declared CLR fixup slot `0x180151b68` contains MethodDef `0x06000ab9`                                                                |
| Managed run                       | MethodDef `0x06000abb` constructs `APICoupler.apiNewConstraintRefplaneCoupler_c`, then generic run `0x06001547` reaches actual `populateDataPacket`, `0x06001551` |

The core creates a real `apiNewConstraintRefplaneData_c`. Relative to that packet, constraints occupy `+0x20/+0x24/+0x28`, their actual doubles `+0x30/+0x38/+0x40`, and count `+0x48`. The public ordinary operation explicitly writes count one. Native and managed bridges preserve these doubles without degree conversion. Angles remain native radians; a signed source angle must account separately for magnitude and reverse.

## Selection marks and constraint construction

Coupler `populateDataPacket`, token `0x06001551`, RVA `0x558dc`, decodes 527 IL code bytes. It obtains actual geometry wrappers and selection marks, requires one to three wrappers, rejects a mark outside `0..2`, rejects duplicate marks, places actual wrappers into the corresponding three slots and retains null for absent geometry. Selection append order does not define the geometry slot.

It sets `ConstrRefPlaneRequest.IsBeingCreatedByAPI`, constructs each selected slot independently through `createConstrainedGeom`, then sets Geometry0, Geometry1 and Geometry2. It requests OK, validates the actual triplet and refuses a pre-apply warning. No native-success conclusion follows from constructing those packets statically.

`createConstrainedGeom`, token `0x06001553`, RVA `0x5537c`, decodes 973 IL code bytes. For the ordinary angle/line input:

| Authored API state                         | Actual construction                                                                                                                                      |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Constraint mask bit `16` on selected plane | `AngleGeom_c(actual slot index, actual selected wrapper, angle, flip, count)`                                                                            |
| Constraint mask bit `4` on selected hinge  | `CoincidentGeom_c(actual slot index, actual selected wrapper)`                                                                                           |
| Mask bit `256`                             | Extracted as `(mask >> 8) & 1` for the angular reverse flag                                                                                              |
| Nonpositive or unordered numeric angle     | Consumer starts at zero and copies the supplied double only when it is greater than zero; a negative scalar alone does not express the opposite rotation |
| Count                                      | Clamped to `1..100`; this public call supplies one; multi-plane semantics are outside the proposed ordinary source profile                               |

The mask branches also support other constraint kinds. This finding does not admit those combinations. Its numeric replay admits only the independently declared ordinary acute-angle plane/line inputs. It refuses duplicate/missing marks, incompatible owners and nonfinite or negative raw angles.

The concrete next API operation is:

1. Retain an actual plane and actual line or reference-axis wrapper lying in that plane. Clear the selection list and verify the exact selected object identities.
2. Select the plane with mark `0` and the hinge with mark `1`, retaining those marks even if append order changes.
3. Call `InsertRefPlane(16 | optional 256, positive_angle_rad, 4, 0.0, 0, 0.0)` for one ordinary plane.
4. Inspect the actual published plane data and selected geometry; do not select an archive class solely from the public API's plane type.

The two protocol inputs are independently authored numeric examples, `0.2173 → 0.3497` radians without flip and `0.4879 → 0.2981` radians with flip. The second reverses append order while retaining marks. Their analytic normals use Rodrigues rotation from actual declared base/hinge vectors; those calculations are conditional mathematical predictions, not observations of SOLIDWORKS's actual sign convention. No held-out design was opened or created by this delivery.

## API-created is separate from old-API plane data

The coupler's current `IsBeingCreatedByAPI` flag does not establish compatibility wire ownership. In `sldcoreu`, `isOldRefPlaneOrCreatedByApi`, token `0x06004de2`, delegates to two separate checks. Token `0x06004de0` asks an actual existing feature for creation version and compares unsigned `<4150`. Token `0x06004de1` obtains an actual existing `moRefPlane_c`, its actual data and `moRefPlnData_c.isCreatedByOldAPI_0`; an absent actual feature/data does not satisfy it. That method does not read `get_IsBeingCreatedByAPI`.

The existing [angular-plane factory record](FreecadCylinderAngledPlanes2026.md) still governs the concrete constrained versus compatibility branch. Its parallel line/plane case uses this actual old-plane predicate; the new public command flag cannot replace it. Current exact API framing now supplies the ordered `AngleGeom` plus `CoincidentGeom` input that the native factory tests, but source correlation must verify the final class and its complete initialization.

## Editable dimension and save/reopen observation

The earlier exact factory trace proves that the plane must own its data before init creates the real angular display, `AngleDim_c`, feature handle and `moAngleParameter_c`, with actual plane owner and role one. Constructor scalar/transform alone is insufficient.

A new author observer must bind the actual parameter freshly from the plane feature's bounded display list, verify angular dimension type, driving/editable status, full owner-qualified name and parameter identity, then edit its `SystemValue` in radians. The existing `ReferencePlaneDimensions` helper is qualified for offset/radial use and routes non-radius mode to linear type; passing an unrecognized `angle` string would therefore be wrong. Extend a private angular-specific observer and its exact registered metadata before execution. `FeatureByName` belongs to `IPartDoc`, not `IModelDoc2`.

Record both original and edited indexed reference constraints, angle values, complete plane/line frames, actual dimension name, tree and native status. Save distinct immutable source/edited siblings. Reopen each in a fresh process and repeat actual owner and dimension checks between healthy controls. A coincident feature name or matching transform without the actual driver and references is insufficient. Zero, mixed-sign and multiple-plane sources remain separate pending probes.

## Selected-end enum boundary

The new exact API image closes the previous missing public extrusion owner: actual feature-manager vtable `+0x7a8 → sldapiu:0x42c43430 → 0x42c43720` calls imported `slduiu!iApiFeatureExtrusion4` at `0x492546e0`. It preserves both supplied end integers. That ordinary branch loads macro fields unchanged into dialog offsets `+0x84/+0xb8`, and actual apply copies them into `moEndSpec` `f0c/f10`.

The pinned reference-acquisition routine `slduiu:0x493e6470` handles native point `3`, selected surface/offset `4/5` and body `7`; a `10` input takes none of those branches. The current `GetEndCondition` body `sldapiu:0x42998cf0` reads the actual dialog's `+0x84/+0xb8` integers directly. No `10 → 4` translation was found on this precisely bounded route. This is not proof of global enum rejection or absence of another author API.

The [selected-end model trace](FreecadCylinderSelectedEnd2026.md) independently binds `ToSurfaceEndSpec.Apply` to native `4`, actual selected wrapper and separately published persistent direction. Therefore the first source experiment can use explicit plane/surface end `4`, profile mark `0`, selected end mark `1` and actual direction mark `16`, and measure the result. Public `swEndCondUpToSelection=10` requires a separate qualified translation/rejection experiment. Do not write native type `10` or retain a blind distance display merely from that enum's public name.

## Replay and limits

```sh
uv run --no-project --offline --isolated --python 3.11 \
  --with dnfile==0.18.0 --with dncil==1.0.2 --with pefile==2024.8.26 \
  python -B re/tooling/sw2026/freecad_cylinder/PinCylinderAngleApi.py \
  --root /absolute/Kit --inputs /absolute/licensed-originals \
  --knowledge re/solidworks/records/FreecadCylinderAngleApi2026.json \
  --protocol re/solidworks/records/FreecadCylinderAngleAuthorProtocol2026.json \
  --output /unused/AngleApiPin.json
```

The tool validates six module identities, both managed MVIDs/flags, complete native unwind functions, 16 full managed methods, actual manager/COM slots, the declared native-to-managed constructor slot, a bounded bridge span and selected executable instruction predicates. It emits numeric and metadata evidence only. Independent successful replays must be identical; malformed module/version/CLI/input cases must fail without publishing a receipt.

This tranche reads no CAD source, produces no CAD output and launches no CAD or disassembler session. Existing frozen direction, selected-end, angular-plane and downstream edge-map packets are preserved. Full source-preserving FreeCAD lowering, display/style/helper-point completion, native angular source locks, combined oblique extrusion and generated held-out acceptance remain unfinished.
