# Ordinary downstream edge validation, SOLIDWORKS 2026

The exact source distinguishes the initial mode trial, same-ID current-row fallback, and repair of an earlier colliding row. For the bounded collision-free ordinary prism, these validators retain the supplied mode-1 reference and its incoming cache fields; they do not clear `fe8`. Native qualification of a generated downstream stream remains open.

Task `B04-SW2026-DOWNSTREAM-EDGE-VALIDATION`, owner `configuration_header`, delivery PR #121. Root owns the positive-fin constructor, generated topology, shared codecs and oracle. The exit condition is a reproducible source checkpoint for the initial validator and post-insert repair, including field retention and unresolved branches. [Numeric ledger](DownstreamEdgeValidation2026.json) · [Source receipt](../measurements/2026/DownstreamEdgeValidationSource01.json)

## Exact source authority

| Original | SHA256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldutu.dll` | `dbc147c10b658544e44a7c13d3ae656c26a0778e9241fe74d6ca9ecae8730933` |

The record pins 32 complete function owners, including chained unwind fragments, 74 checked original intervals, three concrete virtual slots and ten typed imports. All addresses use preferred-image virtual addresses. The [verifier](../../tooling/sw2026/downstream/VerifyEdgeValidationSources.py) reads original bytes without loading a vendor module. No binary, instruction listing, captured CAD row or native payload is included.

This extends the separate [assignment](DownstreamFreshReferenceAssignments2026.md), [conditional role](DownstreamBoundaryRoles2026.md) and [key text](DownstreamFaceKeyOrder2026.md) checkpoints. Their frozen packets remain unchanged.

## Initial trial needs actual face and edge identity

`0x4b525960` receives the actual downstream data, attempted CompEdge and current actual edge. It requires nonnull inputs, the component's actual BEnt reference and that reference's embedded signed `f18.f10` map. Roles 0 and 1 are resolved by `0x4b52d430`:

`role key → allocated face-row ID → data.f340 identity info → checked info.f08 ordinal → data.f6d8 actual face`

The helper checks the parallel actual-face vector, map membership and ordinal bounds. A node ID, face key, arbitrary index or merely nonempty reference is not a substitute for that join.

The two faces' common-edge result is classified as follows:

| Classification | Acceptance |
| --- | --- |
| 0 or error | Reject the trial |
| 1 | Output vector must contain exactly one actual edge pointer, equal to the supplied current edge |
| 2 | Both roles 2 and 3 must resolve to nonnull faces, each different from both adjacent faces |

Classification **2 means two or more**, not exactly two. The direct `gcFace_w::commonEdge` array path saturates every count above one to 2. The helper path has the same classification and can clear its vector on a third match. The second branch does not require the role-2 and role-3 faces to differ from each other. This corrects the earlier prose that described the branch as exactly two; no predecessor receipt is changed. [Saturated-result gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/CommonEdgeResultTwoIsSaturated.md)

For an ordinary rectangular prism, the narrow source rule uses the first branch: actual adjacent faces share exactly the current actual edge. General seam, multi-match and nonmanifold conclusions are not transferred from that rule.

## Active helper and required cache state

Fresh orchestration constructs `tempEdgeHelper` at `0x4b5264f4`, then builds faces before edges. The initial validator checks global `0x4db57ba8`. When nonnull it invokes `0x4b566e10` with the stop-after-multiple argument true; when null it calls the typed direct common-edge import.

The active helper requires actual nonnull faces, an initially empty output vector, and nonnull face-cache globals `0x4db57b98` and `0x4db57ba0`. `0x4b566ce0` looks up the real face pointer. If absent, `0x4b567830` obtains the actual face edges and loop/coedge owners and builds their sets. The common-edge helper intersects unique actual edge pointers. A failed active-helper lookup does not fall back to the direct import inside this validator.

The helper constructor and cache setup have additional model-mode and nested-lifetime branches. This packet binds their complete source owners but does not turn a preexisting global cache into a universal fresh-state constant. A neutral constructor should derive the required actual adjacency from its generated topology, not emit native addresses or depend on these runtime globals. Nested helper teardown and later temporary-map normalization remain separate obligations.

## First fallback, allocation and recorded ID

The fresh edge loop `0x4b52ab60` first attempts `moCompEdge_c(actual edge,actual component,1)` at `0x4b52ad43`. A failed initial validator destroys that trial after removing its reference from the runtime helper, then constructs mode 0 at `0x4b52ae1c`. A local flag records whether the mode-1 trial was retained.

The selected component receives the actual body atom in inherited `f18/f1c`. With nonnull runtime edge vector `data.f6e8`, the caller consumes data `f08` once, appends `(component pointer,allocated ID)` to `data.f60`, appends the actual edge to `f6e8`, records actual edge → row ordinal in `f4c0`, and registers unique info with entity type `0x138a`. Actual body atom, allocated downstream ID, native edge node ID and vector ordinal remain separate domains.

Only a retained mode-1 trial enters post-insert validation at `0x4b52af3a`. An initial mode-0 fallback skips this post-key registration. A false post-insert result constructs a new mode-0 component for the **same current actual edge**, copies its body atom and replaces only `f60[row].pointer` at `0x4b52b011`. The existing row's ID word is untouched. It also marks that row ordinal in the runtime replaced-index set `data.f8e8`; it does not consume another `f08` ID.

## Ordinary original and anti key text

The post-insert validator at `0x4b5251d0` uses the common key wrapper `0x4b526a60`. Actual ordinary part table `0x4d1252d8 +0x1a8` reaches the false leaf, so both original and anti key calls pass a null optional body-index input. The wrapper passes zero for the parameter suffix and representation pointer-metadata options.

Text starts with ASCII `s,` when reference `fe8 &0x4` is clear, or `S,` when set (`0x4b529a88`). There is no separate `e,` prefix. The root's separately established incoming `0x300` has bit `0x4` clear. For each nonnull representation in actual ID-slot order, append its signed decimal data words separated by commas. **Do not add any separator between the individual representation strings.** Skip null representations.

The already-proved ordinary cap data are `[40,FR.feature,signed_low32(FR.epoch),FR.flags&~0x10,cap.selector,cap.contour]`, with negative contour normalized to -1. Side data are `[74,FR.feature,signed_low32(FR.epoch),FR.flags&~0x10,side.marker]`. These inputs belong to the actual generated feature/creation/FR graph. The format rule does not supply captured field rows.

Hash exact logical ASCII text, excluding its terminator and capacity padding. With `h=0,p=1`, for each byte set `h=(h+byte*p)%1000000009` and `p=(p*32771)%1000000009`. The later FNV bucket hash is not the semantic key.

Edge `makeAntiCopy` at `0x4b757720` accepts even ID counts or count 5. For the first four slots it swaps `0↔1` and `2↔3`; count 5 retains slot 4. A separate degeneracy applies when actual `moEntityId` equality says original slots `2==3==1`: anti slots 2 and 3 become original slot 0. It copies `f60/f64/fe8` into the temporary anti reference. This is different from the FaceRef swap of slots 1 and 2. [Anti-key gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/EdgeAntiKeyUsesDifferentSlotPairs.md)

## Post-insert collision state and field retention

The post-insert validator requires a valid existing current row, actual model/edge, nonnull BEnt reference and nonzero original key. Runtime key storage `data.f828` carries key, **row ordinal** and actual edge pointer; it does not map directly to an allocated downstream ID. Its native insertion helper can retain duplicate keys in the broader reconciled path. A collision-free fresh pass never needs that branch.

When neither original nor nonzero anti key exists, it registers the original key and returns true. It does not replace the current row, call `clearEntCache`, or alter the incoming reference `f60/f64/fe8/f70`. For an already nonnull CompEdge `+0xe8` reference pointer, `getRefBEnt` returns that owner directly; its lazy virtual construction is guarded by a null pointer. This component pointer is a different owner from the BEnt's scalar flags at its own `+0xe8`.

When a key exists, helper `0x4b536870` may rebuild and replace the **earlier matching row** with mode 0 before deciding the current reference's ambiguity state. It checks `f6e8`, both row/vector bounds, the prior actual edge/body, and the replaced-index set `f8e8`. Replacement helper `0x4b536710` writes only that earlier row's component pointer and marks its ordinal. Its allocated ID remains intact.

The helper's Boolean result and separate out-status are not interchangeable. The original-key branch accepts the current reference only when the out-status is nonzero. The anti-key branch rejects a nonzero helper return, then otherwise continues to original-key registration. Some direct-match branches update the current reference's `f60/f64` from the newly reconstructed prior reference or its actual candidate list. A general collision implementation requires those full semantics; a unique-key test alone does not qualify it. [Repair gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/EdgeRepairCanReplaceEarlierRows.md)

The useful bounded construction condition is therefore: actual fresh ordinary prism topology; roles 0/1 resolve through the correct face allocation; one common actual edge equal to the current edge; nonnull runtime edge vector; nonzero original key; neither original nor applicable anti key already registered. Under these conditions, the incoming mode-1 reference survives the two validator stages with the same allocated row ID and unchanged flags/cache words. The constructor's `fe8=0x300/f70=0`, if independently established, must not be cleared by an invented post-validation rule.

## Evidence limits

All new rules are source-only and carry `partial` confidence until exercised. This packet does not supply live wrapper handles, prove the root's constructor, normalize alternate model contexts, or qualify helper destruction/final storage. It does not broaden seam/multibody/collision coverage or establish a usable native downstream stream.

No CAD input, original held-out, SDK product process, native process, VM call, shared source edit, application/license action or persistent REA/Hopper target occurred. Earlier option/body/face packets remain unchanged. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), [full playbook](../../Playbook/README.md) and [loader phase](../../Playbook/LoaderAnalysis.md) remain the governing acceptance boundaries.
