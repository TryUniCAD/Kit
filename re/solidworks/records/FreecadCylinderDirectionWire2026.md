# Persistent extrusion direction and selected-plane limits in 2026

This partial source record maps the persistent direction and selected-plane limit construction. Generated-file qualification remains open.

Task `B04-SW2026-FREECAD-CYLINDER`, owner `/root/assembly_occurrence`, delivery PR #121. Root owns the oracle and integration. This continues the [five-driver lowering](FreecadCylinderFiveDriverLowering2026.md). The [knowledge table](FreecadCylinderDirectionWire2026.json) pins 31 logical native functions, nine runtime descriptors, ten call edges and two geometry-dispatch slots. [Replay tool](../../tooling/sw2026/freecad_cylinder/PinCylinderDirectionWire.py) · [Static receipt](../measurements/2026/FreecadCylinderDirectionWire01.json)

## Authority

The original `sldmodu.dll` has 46,536,280 bytes, preferred base `0x4b140000` and SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The array-pointer primitive is in `sldmfcu.dll`, 8,274,520 bytes, base `0x3c720000` and SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`. The scoped build is `34.5.2.0604` with document version `19000`.

The pin tool reads PE exports, runtime descriptors, virtual targets, chained unwind metadata, import identities and bounded instruction ranges. It emits hashes and numeric metadata.

## Live references and literal direction

`moEndSpec_c.f138` is the actual `moDirectionSpec_c` pointer. Its getter `0x4b283bd0` and setter `0x4b30fb20` are direct pointer accesses. The independent `f8c` integer remains extrusion reversal.

The reference-taking direction constructor `0x4c302ac0` delegates to `0x4c302c80`, which allocates a `suObArray` at `f08` and appends the actual selected wrapper. It stores the two supplied option integers in `f10/f14` and clears `f18/f20/f28`. The two-reference constructor uses the same first array owner and appends the second wrapper through `0x4c303070`.

`getUpdatedDirection` at `0x4c3032a0` checks the literal vector pointer `f18` first. A present vector is normalized and takes precedence over selected geometry. Constructor `0x4c302910` creates this literal-vector representation.

With `f18` absent, selected paths obtain current geometry from the wrapper. `moLineRef_w` dispatches through `+0x3f8` to `0x4c316200`, and `moPlaneRef_w` through `+0x338` to `0x4c319570`. The resulting unit direction is a local output. Nonzero `f10` reverses it. Source option `f14=0` uses the primary geometry direction. Public selection polarity still needs measurement.

## Current direction wire grammar

Serializer `0x4c695dd0` supplies the following modern order after the shared object base:

| Order | Wire owner                                                                                                            |
| ----- | --------------------------------------------------------------------------------------------------------------------- |
| 1     | `i32 has_f08`, then shared embedded `rf.suObArray f08` when nonzero                                                   |
| 2     | `i32 f10`                                                                                                             |
| 3     | `u8 has_f18`                                                                                                          |
| 4     | Only when `has_f18`: vector `f18`, `u8 has_f20` and optional vector `f20`, then `u8 has_f28` and optional point `f28` |
| 5     | `i32 f14`                                                                                                             |

The array pointer prefix is a four-byte integer from `suObArray::serializePtr` at `0x3c8cfda0`. The end's surface arrays have their own one-byte gates. In a reference-backed direction the zero `f18` byte skips the entire nested optional geometry branch, including the `f20/f28` gates.

The concrete runtime descriptor has raw schema `0x80000001`, size `0x30` and archive schema one. The `moRefSpec_c` base contributes fields and has schema `0xffff` with no creator. Its destructor deletes the wrapper objects and their array, so separate owning arrays require separate wrapper and component references even when they select the same feature.

## Axis and plane reference closure

For an ordinary registered local axis, the concrete graph is:

`direction.f08[] → moLineRef_w.f58 → moCompRefAxis_c → actual component + feature identity`

`moCompRefAxis_c` constructor `0x4b278b80` delegates through `moCompRefGeom_c` `0x4b7e7980` and `moCompFeature_c` `0x4b815370`. It retains the owning component and feature reference. The registered path uses the actual feature ID and creation record and clears `ff8`. A direct `ff8` geometry owner is retained only while the selected feature ID is `-1`.

Two-plane axis constructor `0x4c27bef0` creates `moPlaneInterAxisData_c` at `axis.f700`. Constructor `0x4c281520` stores the ordered plane wrappers at `f80/f88` and links the live axis owner at `f48`. Serializer `0x4c2744f0` writes the axis-data base and the two actual `moPlaneRef_w` references. The axis backpointer exists at runtime.

For a plane direction or limit, use `moPlaneRef_w.f58` to select a `moCompRefPlane_c` with the actual component and registered plane identity. The wrapper is a subtype of `moSurfaceRef_w`. Arbitrary-axis publication and completed cache state still need source controls. [Wrapper construction](PlanarMateWrapperWriteState2026.md) · [Creation times](ModelConstruction2026.md#feature-reference-creation-time) · [Offset planes](ReferencePlaneOffsetConstruction2026.md)

## The limit plane and the distance have different owners

| Role                             | Actual field/path and branch                                                                                                        |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Forward selected surface or plane | `u8 has_f28` gates the embedded `end.f28` array containing the actual plane wrapper. |
| Reverse selected surface/plane   | `u8 has_f48` gates embedded `end.f48`                                                                                               |
| Up-to-point reference | Forward `f68` when native `f0c==3`, reverse `f70` when `f10==3`. |
| Up-to-body reference             | `f78/f80` under the corresponding native type `7`                                                                                   |
| Forward or reverse length or offset | `f18/f20` are display object pointers. `getDistance` at `0x4badf660` follows the selected display to its value. |
| Proposed vertical `Height`       | The selected height plane's real offset display/parameter, such as the existing `moFaceRefPlnData_c.f98` route                      |
| `fa0` | A separate serialized double with its producer still open. |

`setISurfRef` at `0x4baf92d0` selects `f28` or `f48`, optionally clears it and appends the supplied wrapper uniquely. Termination, direction and display come from separate setters. Serializer `0x4bb10250` writes the direction and displays and uses individual conditions for point references and surface arrays. A zero array gate skips its field on load. Ordinary store derives the gates from archive and model context.

The public `swEndCondUpToSelection=10` mapping to native `f0c` and the selected-plane factory's inactive distance display state remain open.

## Concrete construction sequence and remaining gate

1. Construct and publish the two angle-controlled planes and their intersection axis with actual feature IDs, creation records and model ownership. The angle-plane construction itself remains a separate unfinished dependency.
2. Create a fresh axis component reference and line wrapper, then the reference-taking direction owner with absent `f18/f20/f28`. Verify the direction polarity against the authored local positive Z.
3. Construct the height plane from source `Height` through its real offset driver. Create a separate actual plane wrapper for the selected end, preserving the complete source Placement.
4. Attach that wrapper to the correct end surface array with its present gate. Construct the separately bound native end mode and display lifecycle after source evidence establishes them. Keep unused point/body branches inactive.
5. Attach the direction at `end.f138`. Register actual dependencies: native `getRefWrappers` includes limits, direction selections and from-end references, so a profile-only feature parent list is insufficient.
6. Use the shared allocator, component ownership, array/object/map primitives and computed wrapper geometry. Never substitute stored vector data for the selected feature or use a captured cache/default from a saved part.

Before writer implementation, lock the non-normal source cohort and measure axis and plane direction, selected-end enum and displays, five live edits, full and partial sweep and retained metadata. The current replay verifies the source binding. [31-function replay](../measurements/2026/FreecadCylinderDirectionWire01.json)
