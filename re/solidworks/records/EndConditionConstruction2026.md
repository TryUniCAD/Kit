# Extrusion end-condition construction in 2026

## Scope and authority

This record extends the ordinary blind construction in [ProfileConstruction2026.md](ProfileConstruction2026.md). It separates the native object's field ownership from public API codes and from measured writer acceptance. The original installed `sldmodu.dll` has SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` and preferred base `0x4b140000`. Addresses below belong to that exact image. Analysis uses its export aliases, PE exception/unwind metadata and bounded instruction ranges; proprietary images and listings remain outside the checkout. The REA session reports no open target and pending provider cleanup, so its native analysis is unavailable; the installed LLVM/PE fallback supplies the static observations.

No new end-condition writer has been implemented from these observations. A separate complete 2026-authored corpus must lock before that work. Source creation, source edits, source round trips and static ownership do not count as generated-output or held-out acceptance.

## Native ownership

| Member | Owner and rule | Original 2026 authority | Confidence |
| --- | --- | --- | --- |
| `f08` | Single-end integer, directly read and written without translation by `getSingleEnd` / `setSingleEnd` | `0x4b283ba0` / `0x4b2913b0` | Confirmed static ownership; full legal domain remains partial |
| `f88` | Independent flip integer, directly read/written by `getFlip` / `setFlip` | `0x4b2a75e0` / `0x4b2a7860` | Confirmed static; public cut-side mapping needs separate evidence |
| `f8c` | Independent direction integer, directly read/written by `getDirection` / `setDirection` | `0x4b2c47a0` / `0x4b2c69a0` | Confirmed static; public reversal mapping awaits corpus reconciliation |
| `f0c`, `f10` | Two consecutive `gcEndSpecType_e` integers selected by end index, with no getter/setter remapping | `getType` `0x4b30d800`; `setType` `0x4b3100b0` | Confirmed static ownership; public enum equivalence remains partial |
| `f18`, `f20` | Actual forward/reverse distance display nodes; `getDistance(index)` follows the selected display's model handle and reads its value, or returns zero for a null display | Complete unwind range `[0x4badf660,0x4badf691)`; handle getter `0x4c8845a0`, value getter `0x4c844d80` | Confirmed static |
| `fc8`, `fd0` | Corresponding angular display nodes used by `getAngle(index)` and `setAngle` | Complete getter `[0x4badf020,0x4badf054)`; setter `[0x4baf9160,0x4baf91af)` | Confirmed static |
| `fb8`, `fbc` | Consecutive draft-enable integers selected by end index | `getDraftCheck` `0x4b30bd90` | Confirmed static |
| `fc0`, `fc4` | Consecutive draft-direction integers selected by end index | `getDraftDirection` `0x4b30bda0` | Confirmed static |

These offsets are relative to the actual `moEndSpec_c` receiver. Folded export aliases still identify the same instructions; an unrelated nearest symbol printed by disassembly does not change the receiver's proven export identity.

## Geometry boundary and setter lifetime

`genGcEndSpec` has complete unwind range `[0x4bade750,0x4badf01a)`. It reads both distance and angle values from their actual model handles, then passes the single-end value and address of the two end-type integers to `gcEndSpec_c::setEndSpecData`. The import at `0x4cd368a0` resolves to that exact exported method in `sldgcu.dll`. The pointer arrays for angles and draft flags are distinct. This establishes that the fields participate in the geometry request; it does not establish the meaning of every enum or that an arbitrary combination rebuilds.

`setDistance` is split across three chained runtime-function ranges: `[0x4baf91b0,0x4baf91dd)`, `[0x4baf91dd,0x4baf9288)` and `[0x4baf9288,0x4baf92bd)`. Its first PE range alone is incomplete. The forward branch can inspect and unshare a shared thickness parameter before updating the display; the reverse branch updates its selected model handle. The fresh non-sheet-metal writer must retain its independently constructed parameter graphs. These observations do not authorize copying saved dimensions, sharing parameters implicitly or treating a scalar as a display node.

## Independent source targets

The [end-condition source specification](../../tooling/sw2026/EndConditionSpecs.json) chooses twelve rectangular discovery inputs and four circle held-out inputs before writer changes. The forward/reversed ladders isolate reversal with matching section and depth; the mid-plane ladder changes termination; the two-direction ladder varies independent depths and also reverses one case. Two controls use independent rectangle and point-circle creation.

Let the sketch section have area `A`, perimeter `P` and centroid `c`; its unit world normal is `n`. A blind interval is `[0,d1]`, mid-plane is `[-d1/2,d1/2]`, and two-direction blind is `[-d2,d1]`. Reversal maps `[a,b]` to `[-b,-a]`. Independently expected volume is `A*(b-a)`, surface area `2*A+P*(b-a)` and center of mass `c+n*(a+b)/2`. These formulas are measurement targets, not fitted stream caches. Both native definition read-back and geometry must agree. The new lock and discovery archive reconciliation remain pending; held-out native payloads and siblings must not be read during derivation.

The [complete corrected source lock](../measurements/2026/EndConditionSourceLock02.json) now records all sixteen passing cases, 38 fresh phases and 437 numeric checks with healthy controls and unchanged licensing identities. All eighteen native hashes and 32 sibling hashes were verified before new end-condition writer work. The first incomplete attempt and its harness owner bug remain separate. The [prepared discovery/control set](../measurements/2026/EndConditionPreparation02.json) contains fourteen inputs and excludes held-out payloads. Public API read-back is now measured; archive-to-native-field reconciliation remains pending in remote CI. No enum mapping or new writer acceptance is inferred from source API observations alone.
