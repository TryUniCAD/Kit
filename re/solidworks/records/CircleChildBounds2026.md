# Ordinary circular child bounds and target admission

The internal SDK now constructs child-local bounds for one forward Front circular blind boss from its actual generated `CirclePlan` owners. Twenty-three SDK processes pass. Native assembly and concentric-writer acceptance remain unqualified. The six disclosed saved child caches match 58 of 60 independently calculated words; both D03 low-y extrema differ by one ULP. No saved-value adjustment is introduced.

Task `B04-SW2026-MATES-CONCENTRIC/circle-child-bounds`; owner `assembly_occurrence`; delivery PR #121. Base source is `46f5562987bdb8203d7f36e6ba5acbf52bdd4e92`. Dependencies are the existing [fresh cylinder owner audit](FreshCylinderEndpointIdentity2026.md), shared `CirclePlan`/part construction, ordinary target contracts, the [native point-pair bounds rule](AssemblyConstruction2026.md#computed-geometric-bounds), and the already disclosed D01–D03 child/parent saves. This tranche exits at a guarded internal target, exact regression and saved-owner correlation. Root owns kernel/face construction, VM execution, native qualification and shared registers.

[Sanitized receipt](../measurements/2026/CircleChildBoundsSdk01.json) · [Native source facts](CircleChildBoundsNative2026.json) · [Constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Bounds/Circles/MakeCircleBox.py) · [Process replay](../../tooling/sw2026/RunCircleChildBounds.py)

## Native ownership and sphere policy

Pinned original `sldmodu.dll` supplies the part vtable at `0x4d1252d8`. Slot `+0x1350`, used by the reference update, selects the wrapper `[0x4b57a7e0,0x4b57a82c)`. It supplies a zero extra mode and jumps to the shared model getter `[0x4b581040,0x4b581568)`. In its ordinary cached branch, `0x4b5811ed` obtains model member `+0x7f8`; calls at `0x4b5811f4` and `0x4b58120c` use `mgBBox_c::isSet` and `operator|=`. The initially unset result retains the complete source box, including its independently stored sphere. The alternative configuration/exploded/3D-box paths are not generalized here.

The body branch calls imported `gcBody_w::getBBox` at `0x4b581321`. The native edge continues through the geometry thunk `0x4388ecd0`, dispatch `[0x43e816e0,0x43e8170e)`, and `sldgciParau!gciBody_w::getBBox` `0x32f80ef0` to `gciTopEnt_w::getBBox` `0x33096440`. On successful raw box retrieval, `0x330964d2` calls imported `mgBBox_c::set(double*)`. That setter `[0x31de8760,0x31de87e7)` passes the two three-coordinate corners to the point-pair setter `0x31de85b0`. The latter explicitly stores the corner midpoint, computes the three-coordinate diagonal and stores half its length. The receipt pins four original modules, nine code ranges, four direct edges and five imported edges. The indirect geometry jump has a REX prefix and is seven bytes; the collector decodes its actual instruction length.

The sphere therefore follows the native box constructor for this profile. It is larger than the minimum enclosing sphere of the physical cylinder. Once constructed, its center/radius stay separate from low/high corners; the existing parent placement and union rules preserve and merge that sphere. Do not substitute a sphere recomputed from a rotated aggregate's extrema. [Existing union evidence](OrdinaryOccurrenceConstruction2026.md#generated-ordinary-occurrence-process)

## Model derivation

All coordinates below are in metres. The supported actual profile frame is the positive Front identity frame. Let the actual circle center be `(cx, cy)`, radius `r > 0` and live forward blind depth `d > 0`:

| Wire fields | Rule                                                               | Classification                                      |
| ----------- | ------------------------------------------------------------------ | --------------------------------------------------- |
| `b3,b4,b5`  | High corner `(cx+r, cy+r, d)`                                      | Derived from authored geometry and termination      |
| `b6,b7,b8`  | Low corner `(cx-r, cy-r, 0)`                                       | Derived from authored geometry and termination      |
| `b0,b1,b2`  | `(low+high)*0.5`, retaining actual binary64 arithmetic             | Derived sphere center from native point-pair policy |
| `b9`        | `0.5*sqrt(dx*dx + dy*dy + dz*dz)`, with each difference `high-low` | Derived native box-sphere radius                    |

The implementation delegates the ten-field arithmetic to the existing `MakeBox`, preserving its finite-domain checks and arithmetic order. It never reads a file, cache or saved row. Radial dimension presentation does not alter the geometric formula. Top/reversed/mid-plane/two-direction cases, shifted frames, cuts and alternate owners remain refused. Current public assembly child preparation still requires its qualified dimensioned rectangle; this internal target does not register a circular or concentric writer.

[Process receipt](../measurements/2026/CircleChildBoundsSdk01.json) · [Pinned native facts](CircleChildBoundsNative2026.json) · [Saved-cohort auditor](../../tooling/sw2026/AuditCircleChildSavedBounds.py) · [Process replay](../../tooling/sw2026/RunCircleChildBounds.py)

## Actual graph admission

`MakePartTarget`, `TargetDocument` and `CheckAsmChild` retain their existing contracts and code. Only `MakeChildBox` gains a separate `CirclePlan` branch. The ordinary line-loop branch stays unchanged.

The new branch requires the actual complete `PartCandidate`, exactly ordered system/profile/boss roots, one uncut circle plan, Front support and a forward blind end. It binds the profile, actual owning part, real principal datum, reference component and stored inverse frame. Actual point/arc array members must retain the same center, seam and sketch aliases; detached geometry mirrors and changed plan radii are refused.

The end check follows real display → handle → dimension → parameter ownership, with four distinct local end roles. Both lengths must equal the actual driving depth; inactive draft angles and the from-end value must be zero. Foreign parameters, aliases, inactive independent lengths, draft controls and a stale primary depth fail closed. The complete end record must still equal the known blind construction and point to those actual displays. This closes a guard missing from the earlier nineteen-process proof without changing any accepted output bytes.

The returned target retains the actual root, configuration, header, Config/Resolved graphs, streams and bytes. It receives a freshly computed local bounds mapping. The target does not gain a body atom, a kernel face ID, a faceted snapshot or concentric wrapper acceptance.

## Disclosed correlation and exact limits

The auditor reads only the previously disclosed D01–D03 source/edited child and parent siblings, with their exact hashes anchored to the existing kernel owner receipt. It obtains radius and local placement from the actual typed cylindrical surface and axial limits from its two actual cap planes. Both occurrence `f370` caches reproduce all ten actual child `f7f8` words in every state: 120 exact words. Occurrence rotation/translation does not enter the child-local cache.

The independently computed physical extrema and native point-pair sphere reproduce 58 of 60 child words exactly, including every sphere center/radius word. D03's source and edited low-y values are each one ULP lower than direct `cy-r`, an absolute `4.336808689942018e-19 m` difference. The underlying kernel extrema rounding operation remains partially traced. The generic kernel box retrieval and native sphere construction are bound, while no case-specific constant, rounding patch or copied cache is admitted to the writer. The six sources remain byte-identical. These are disclosed correlation results, not held-out or new native acceptance.

## Process proof and use

The final host proof runs 23 independent SDK processes: two new circle targets, two preserved baseline circle refusals, four rectangle current/baseline workers and fifteen malformed-target refusals. All four complete circle/rectangle part and stream pairs are byte-identical to baseline. Both rectangle target dictionaries and aliases are identical. Circle targets match independent caller-space extrema/sphere predictions and preserve all actual target owners. The existing public rectangle-child projection still rejects both circle documents.

The generation boundary denies file opens, process launches and network connections after required source/codec imports and actual capability-walker initialization. Every worker records zero attempts. The native cache auditor is a separate read-only phase; no vendor file is an input to generation. Two stateless original-PE collectors produce identical receipts. No VM, COM, hidden input, Hopper session or new assembly file is used. Eight changed SDK files pass Black, Ruff, strict Mypy, strict Pyright, steering and the replay scan. Pyright's three inherited unrecognized settings remain explicit limits.

Run `RunCircleChildBounds.py` with `--root` for the frozen overlay, `--baseline` for the original SDK, `--factory` for the existing `FreshCylinderInput.py`, `--inputs` for [the independent caller cases](../inputs/CircleChildBoundsCases01.json), and a new `--output`. `AuditCircleChildSavedBounds.py` separately takes the disclosed `--packet` and exact prior `--kernel-audit`. `CollectCircleChildBounds.py` takes the existing pinned `--support` PE reader and licensed `--binaries` directory outside the checkout. The private checksum-bound handoff supplies exact replay arguments and full source/input/tool fingerprints.

Fresh whole-assembly open/rebuild, linked child persistence, native field preservation and blinded generalization remain root-owned acceptance work. [Sphere policy gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/CylinderChildSphereUsesBoxDiagonal.md) · [Change entry](../../../Documentation/Changes/Solidworks/Construction/Assembly/Bounds/SolidworksCircleChildBounds.md)

Replay against explicit current/baseline SDK roots and the previously frozen independent caller factory:

```sh
python re/tooling/sw2026/RunCircleChildBounds.py --root /path/to/current-sdk --baseline /path/to/baseline-sdk --factory /path/to/FreshCylinderInput.py --inputs re/solidworks/inputs/CircleChildBoundsCases01.json --output /unused/CircleBoundsProof
```

The private handoff binds exact roots, interpreter, factory hash and unused replay destinations. The input file contains only independently authored values. The product constructor receives actual nodes and reads no research input file.
