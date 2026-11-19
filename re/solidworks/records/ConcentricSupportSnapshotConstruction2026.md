# Concentric support snapshot construction in SOLIDWORKS 2026

Fresh writer acceptance is pending. This is exact-build static construction knowledge plus twelve disclosed endpoint correlations; no generated assembly was opened or measured in this tranche.

Task `B04-SW2026-MATES-CONCENTRIC`; owner `/root/flag_ownership`; delivery PR #121. Dependencies are the [actual kernel owners](ConcentricKernelFaceIdentity2026.md), [active and support reference domains](ConcentricFaceIdentity2026.md), ordinary occurrence placement, and the shared typed archive. This tranche's exit is a complete direct-face snapshot field rule, concrete optional-axis ownership and a precise remaining creation-policy boundary. It does not enable a writer. Root owns integration and the oracle.

[Exact numeric evidence](ConcentricSupportSnapshotConstruction2026.json) records nineteen complete functions, eleven direct call instructions, seven instruction windows and four RTTI-bound primary tables. All addresses below use original `sldmodu.dll` `34.5.2.0604`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`, machine `0x8664`. Full function extents include every contiguous chained unwind fragment from the declared PE exception directory, rather than raw `.pdata` padding or the nearest displayed export label. The evidence contains metadata and independently authored rules, not vendor bytes or listings.

## Actual mate support producer

The path is selected by an ordinary face-backed cylinder wrapper, not inferred from the general graphics helper:

1. `moMate::setViewOnlyRefWrapper` `[0x4bc7f480,0x4bc7f61e)` requires the applicable non-view-only mate state, an assembly owner, a non-null selected wrapper/component and no already installed component view reference. It initializes body, face, edge and vertex outputs to `-1` and identity text to empty. Call `0x4bc7f56b` enters `moAssembly_c::getViewOnlyRefWrap`.
2. Assembly helper `[0x4b69e2f0,0x4b69e527)` prepares the real view-only component and dispatches selected component slot `+0x3f0` at `0x4b69e491`. Actual `moCompFace_c` RTTI/vtable `0x4ce05780` binds that slot to `[0x4b800bc0,0x4b800fa9)`.
3. The face helper resolves the selected face through `getFace` at `0x4b800c2c`, obtains its actual kernel node ID at `0x4b800c40`, and obtains its face identity text through call `0x4b800c63 → 0x4be98610`. The cylindrical branch additionally requires the selected wrapper's applicable cylinder/slot predicates. Call `0x4b800d45 → 0x4b68f110` makes the detached support cylinder. The body result comes from the selected component's actual body and `gcBody_w::getAtomId` at `0x4b800f04`. The ordinary mate caller does not request the separate tessellation output.
4. `moAssembly_c::createNewCylinderRef` `[0x4b68f110,0x4b68f350)` queries the selected wrapper's actual point, unit axis and radius. It constructs an anonymous `moRefCylinder_c`, owned by the assembly self component, and an actual `moCompRefCylinder_c`, sets its viewer ownership and selected face identity, then constructs its `moCylinderRef_w` at call `0x4b68f2f9`. This support geometry uses the selected world cylinder, not a reused child record.
5. Back in the mate helper, `0x4bc7f5c9 → moCompRef_c::setFacetedDataForViewCompRef` `[0x4b806a40,0x4b8070b7)` receives those body/face/text outputs and the new support component. The active receiver is a `moCompFace_c`, whose slot `+0x218` is the independently bound true-return leaf. This selects the direct-face branch.
6. That branch leaves its fresh local point array null and its count zero. At `0x4b806b32` it calls the member constructor `[0x4b7e9c60,0x4b7e9dc0)` with actual body/face/text, null tessellation, and the absent non-face roles below. At `0x4b806b3c` it publishes the new object into the support component's `+0xb0`. Mate call `0x4bc7f5da → [0x4bc7f390,0x4bc7f47e)` publishes the support wrapper under its actual endpoint ordinal.

The resulting owner is `moMateConcentric.f3c8[ordinal].o → moCylinderRef_w.f58 → moCompRefCylinder_c.fb0 → moFacetedData_c`. The active face reference remains a separate graph under `f410`.

## Complete selected snapshot fields

| Field | Class / construction role | Rule and provenance | Confidence |
| --- | --- | --- | --- |
| Point array and runtime `f10` count | Derived | Fresh direct-face local array is untouched/null; count is zero at the actual constructor call. No points are needed to encode this face selection | Confirmed: producer branch plus all twelve disclosed records |
| `has_points` | Derived wire framing | Native store writes unsigned-16 `1` exactly when `count` is `1` or `2`; otherwise `0`. At zero it writes neither the count nor point triples | Confirmed: store instructions `0x4b7ec454–0x4b7ec4af` plus disclosed zero branch |
| `f40` | Derived face identity | Actual selected `gcFace_w` kernel node ID, separately resolved from the constructed child kernel graph | Confirmed; does not equal a required transmitted index or neutral array ordinal |
| `f44`, `f48`, `f4c` | Native branch literals | Each `-1` because the selected role is a face, with no edge, vertex or edge-type role. Argument stores `0x4b806b07–0x4b806b1f` prove these choices | Confirmed for this direct-face branch |
| `f14` | Native branch literal | `0`, the direct face is not a silhouette. Constructor argument at `0x4b806b02` | Confirmed for this branch |
| `f50` | Derived body identity | Actual selected body's atom ID, also the actual generated extrusion atom's `f140` in the ordinary one-body profile | Confirmed; persistent feature ID is a different domain |
| `f54` | Native branch literal | `-1`, because this snapshot does not select an independent feature role. Argument at `0x4b806afa` | Confirmed for this branch |
| `f58` | Derived text | Use the actual selected face's surface identities. For the already bound ordinary single lateral representation: concrete class name + comma + decimal actual extrusion ID + comma + decimal actual arc permanent marker + comma-space-newline | Confirmed for this ordinary single-lateral text; general multi-surface ordering remains outside scope |
| `f58_empty` | Derived wire framing | Signed-32 `1` iff actual CString length is zero; otherwise `0` followed by the actual CString | Confirmed: `0x4b7ec503–0x4b7ec52f` |
| Runtime tessellation handle `+0x18` | Volatile / runtime-only here | Null argument at this constructor call; ordinary modern store does not serialize that runtime handle | Confirmed store rule; no omission/recovery claim for another snapshot |

The member constructor receives points, count, tessellation, body ID, face ID, edge ID, vertex ID, edge type, silhouette, feature ID and text in that order. It assigns separate object members rather than deriving all IDs from one integer. Its full-body SHA-256 is `5492eccbe5d9b8471488fbf53d8f548d228d52499a1e804e6a3c5f03a753ead2`. The empty constructor's `-1` values do not justify replacing the actual face/body values or omitting this populated object.

## Ordinary 19000 wire and older read gates

`moFacetedData_c::Serialize` is `[0x4b7ec410,0x4b7ec8fa)`, SHA-256 `eab7148eac1cfad569ed64b1b604a6fe31d488f945a48a399bc2b687a58ca6d1`. After the shared base call, current store emits:

`u16 has_points; if present: i32 count and count mgPoint triples; i32 f40, f44, f48, f4c, f14, f50, f54; i32 f58_empty; if not empty: CString f58`

The loader has historical gates: point-presence word from `10206`, explicit point count from `11162`, body ID from `10203`, feature ID from `11135`, and identity text from `11216`. Older runtime tessellation/transform paths exist before `10203`. Ordinary `19000` takes the modern layout above. This record does not qualify those legacy modes, an invalid point count, noncanonical framing or a broader database/archive context.

## `f108` is a separate cylinder-wrapper owner

`moCylinderRef_w+0x108` is a pointer to a private `0x68`-byte orientation-history state. It is not a field of `moFacetedData_c`. No native class name or RTTI for the private state is claimed.

The concrete wrapper constructor `[0x4c3073c0,0x4c3074f2)` writes a null pointer at `0x4c30744c`. Its reached update `[0x4c325b80,0x4c325c64)` queries the cylinder and does not allocate that state. The actual support path above therefore has a null constructor state. That path agrees with all twelve disclosed support wrappers.

Actual `moCylinderRef_w` primary table `0x4cd938c0`, bound by its own complete-object locator/type descriptor, maps slot `+0x328` to `[0x4c331bf0,0x4c331cb3)`, SHA-256 `aa050e3ac6b80c234ed6bb1b11e12eb52c8ad1cb07cbb2515ed9192586b3b197`. This is a concrete Boolean operation:

- False clears the pointer and destroys the old state
- True with an existing state retains it
- True with no state allocates `0x68` bytes and calls `[0x4c306c60,0x4c306ded)` with the current wrapper world axis, world point and actual wrapper

The private constructor copies the world axis into state `+0`, world point into `+0x30`, initializes the local axis/point, then tests actual wrapper slot `+0xa8`. If that same-model predicate is false and actual wrapper `f10` exists, it computes the inverse of `f10` and writes transformed unit axis to state `+0x18` and transformed point to `+0x48`. It clears state Boolean `+0x60`. Thus, for the supported rigid occurrence branch, the operation-derived serialized vector is:

`local_axis = unitVector(world_axis * inverse(actual_occurrence_transform))`

Translation does not affect the direction. The mathematical value is model-derived; this tranche does not prove identical signed-zero bits for an independently implemented floating-point transform. Same-model and null-transform default branches are not a generalized source recipe.

Wrapper serializer `[0x4c26f8f0,0x4c26fb27)`, SHA-256 `5e17aecfbac53fb7b0b1c55192c3fac47196f956312386c1a3a73889db3bf96b`, first serializes its surface base, point, axis and radius. It then writes unsigned-16 `0` for null state, or `1` followed by state `+0x18` as a vector for present state. It does not write the whole private state or the wrapper world axis here. The optional state read gate is `4171`; historical presence at least `2` also reads a point, while this current store emits only `0` or `1`.

`getCylinder` `[0x4c313b70,0x4c314096)` can call private consumer `[0x4c309960,0x4c309b31)` when state exists and the applicable special-component branch does not bypass it. That consumer can retain or replace state `+0x18`; unconditional preservation across general geometry changes has not been proved. There is no allocation of the state in this getter.

## Disclosed corroboration and kept gaps

The data-only source is the hash-bound D01–D03 graph SHA-256 `5a28338afa61c3b71daa0059970321e8134b3ace275ebc6f3f36dac0fef8ce4b`. Six original/edited assembly states provide twelve endpoints. The evidence independently joins the actual `f410` face and ordinal-matched `f3c8` support, verifies concrete classes, computes identity text from the actual embedded FRData/FR and marker owners, and corroborates all selected snapshot branch choices. Every support wrapper has no optional orientation vector. Every active wrapper has it. D03's rotated world axis differs from its stored child-local vector, corroborating the transform domain rather than a saved-axis constant.

The remaining active-presence question is precise: the actual vendor selection/creation caller that invokes this concrete wrapper's `+0x328` operation has not been recovered. The constructor and value rule do not establish that every newly selected cylindrical mate must call it. Observed presence in twelve rows does not close that policy. A proposed generator can explicitly model the known enabling operation after geometry/placement initialization, but native acceptance and independent held-out qualification must remain pending until root measures it. No `-Z` vector or repeated face/body number is supplied as a default.

No new CAD invocation, VM action, hidden input read, schema/codec execution, local test or shared worktree edit occurred. No Hopper session was opened. Original image metadata and bounded native instruction analysis were read statelessly. The private static observer first encountered an embedded-FRData reporting error; it was corrected to follow the actual embedded owner without changing a product reader or any input. This is evidence collection, not a CAD result.

The next separate follow-up is the actual face entity tag and the cylinder common surface bounds. Neither is silently folded into the closed faceted snapshot rule. Full fresh concentric native/held-out acceptance remains open. The governing stopping conditions are: “The first is success under every criterion on this page.” and “The second is the end of the available context.”

[Optional-axis ownership gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/CylinderOptionalAxisNeedsItsOwnState.md) · [Change entry](../../../Documentation/Changes/Solidworks/Construction/Assembly/SolidworksConcentricSupportConstruction.md)
