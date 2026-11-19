# SOLIDWORKS 2026 part body count and update-state ownership

A positive kernel body count does not prove publication into the model's retained atom graph. The ordinary part loader can subsequently invalidate the model and clear its body association. The disclosed generated count word is also different from the completed native store, but that difference alone does not select the invalidation branch.

Task: `B04-SW2026-ORDINARY-PART-PARTITION-LOAD`, owner `/root/flag_ownership`, delivery PR #121. The root owns integration, the VM and native experiments. This source-only slice closes the saved-count producer, its actual loader comparison and immediate update-state setters. Actual cold-load operands, first failed atom selection and complete candidate acceptance remain open.

The CAD success criteria and complete RE playbook govern this work. Source spans use original SOLIDWORKS 2026 SP05.2, version `34.5.2.0604`, ordinary archive version `19000`. Pinned module hashes, complete exception groups, selected imports, RTTI and vtable cells are in the [numeric record](PartBodyAdmissionState2026.json). No vendor binary, instruction listing, saved payload, schema execution, SDK execution, test or native/VM action is part of this delivery. The preceding [warning-owner record](PartRebuildWarning2026.md) stays immutable.

## The count is a real signed CMgr field

The actual 2026 `moBaseConfiguration_c` serializer is `[0x4c217e30,0x4c21b8b9)`, 14,985 bytes, SHA-256 `fc50718da7ee40aa89e63a6ee9767c22614373eddab5e942d9e8c105e0e6315a`. Its primary vtable `0x4d027498`, slot `+0x28`, selects this body. The current `SerializeMap2026.json` is a discovery reference; an older unversioned map has different addresses and is excluded from this proof.

On store, `0x4c218394–0x4c2183a2` copies old `+0x6f8` to the separate runtime previous-count field `+0x6fc`. When the configuration is current or does not need rebuild, and its opened model is a nonnull actual `moPart_c`, `0x4c2183ec` invokes that part's `+0x12b0` slot with a null feature argument. The result replaces `+0x6f8` at `0x4c2183ef`. The archive writes this field as a signed `i32` at `0x4c218400`. Other branches retain the prior value; there is no unconditional constant-one rule.

Actual part slot `+0x12b0` resolves to `[0x4c1b0580,0x4c1b0599)`. It loads the real atom manager at part `+0xd88` and forwards to `moAtomManager_c::getNumberSolidBodies(visFilter=0, feature=NULL)` at `0x4bcf7a10`. A missing manager returns zero. The complete getter has conditional runtime body-cache shortcuts and an actual `getBodies` fallback. This result is not a universal raw array length independent of model mode.

On load, version `>=0x72c` reads signed `i32` into `+0x6f8` at `0x4c218f33`, then copies it to `+0x6fc` at `0x4c218f45`. `getPreviousNumberSavedBodies` and `setPreviousNumberSavedBodies` access `+0x6fc`, not `+0x6f8`.

The SDK already preserves this exact raw field through `ConfigurationFields` as `Scalar("f6f8", "i32")`, reached by `ReadCmgrMut` and `WriteCmgrMut`. The research grammar has the equivalent `Vgt(0x72b)` gate. Fresh configuration construction seeds zero; completed-store mutation is a separate lifecycle step. This source inspection does not rerun or extend SDK admission.

## The later comparison can clear an accepted body

`moPart_c::loadExternalBodies` is `[0x4c23e4f0,0x4c23f778)`, SHA-256 `c1182102c7c3336019c2945f76cf1d350ae1c3df0a4649e89583ceecdf4ace8f`. At `0x4c23e5fe` it reads the selected configuration's `+0x6f8`, preserving it in `dword[RBP-0x80]`.

At the exact pre-instruction site `0x4c23f589`:

| Value | Actual domain |
| --- | --- |
| `RSI` | Actual `moPart_c` receiver |
| `EBX` | Signed expected count from configuration `+0x6f8` |
| `EAX` | Completed 32-bit sum, with normal native wrap semantics |
| `ECX` | Legacy extra contribution; zero for the selected version-19000 branch |
| `R15D` | Saved archive version |
| `RBP` | `RSP + 0x100` at this site |

The sum is `dword[RSP+0x74] + ECX + dword[RSP+0x70] + dword[RSP+0x5c] + dword[RSP+0x58]`. The two `+0x70/+0x74` slots are initialized together at `0x4c23ed2c` and are written from actual partition `getBodies` results at `0x4c23f22b`. The other two slots start zero at `0x4c23ed20/0x4c23ed28`; capture every operand rather than substituting a predicted value. The current-version path initializes `ECX=0` and skips the fallback body loop for version `>=0xc7d`.

The signed `jle` at `0x4c23f58b` skips invalidation for `expected <= sum`. If `expected > sum`, `0x4c23f59e` calls actual part virtual `+0xb8(5,0,NULL)`, then `0x4c23f5b7` calls `replaceBody(NULL,1,0,NULL)`. A separate null body element takes `+0xb8(1,0,NULL)` at `0x4c23f1b4` and the matching clear at `0x4c23f1cd`.

The root's data-only disclosed audit reports generated `f6f8=0` and saved/control `f6f8=1`, with actual configuration pointer identity retained. Both generated parts have model `f0c=0/f2c=0x100`; the three saved/control states have `f0c=0/f2c=0x8120`. This is an observation of distinct owners, not a constant whole-word recipe. Expected zero cannot by itself trigger `expected > sum` for nonnegative sum one. The later aggregate and the actual atom-publication path still need measurement. The prior same-phase kernel count-one/public-body-zero result remains a failed model admission, despite diagnostic completion.

## Exact update-state setters

| Owner | Source-backed operation |
| --- | --- |
| `moNode_c::setNeedsUpdate`, `0x4c03ed90` | After accepted guards, nonzero argument writes `(old & 0xfffd7ff9) | 1`; zero argument writes `old & 0xfffd7ff8` |
| `moNode_c::setUpdateError`, `0x4c03ef10` | Nonzero writes `(old & 0xfffd7ffa) | 2`; zero returns without writing |
| `moModel_c::setNeedsUpdate`, `0x4c0363c0` | Conditional sensor notification, then the actual node setter; no direct `+0x2b8` invalidation |
| `setNeedCacheModUpdateStatus`, `0x4c0362e0` | Writes `+0x2b4`; a zero argument also clears `+0x2b8` masks `0x1/0x2` |
| `setNeedsCachedUpdate`, `0x4c036390` | Argument exactly one writes `(old & 0xfffffffd) | 1`; every other value writes `(old & 0xfffffffe) | 2` |

A nonzero node update request can be suppressed by actual `GetDebugNoRegen` or a protected feature state. The original getter `sldgcu!0x439d3df0` tails to `0x43e73670`, a direct `gcEnvironment+0x1e4` read. There is no debugger API in this getter; its upstream writers and any runtime timing effect are separate, unproved boundaries.

The actual model constructor sets `+0x2b4=0` and `+0x2b8=0` at `0x4c00effa/0x4c00f005`. These are runtime cache fields, not a newly inferred wire layout. Actual part `+0xc0` can use cached `+0x2b8 & 1` when `+0x2b4` is nonzero. The direct setter search is bounded to original `sldmodu .text` and cannot exclude inline, indirect or other-module mutations. The immediate `+0xc0`, node needs-update and update-error bodies do not directly read `f2c`; this does not exclude effects in their callees or earlier lifecycle owners.

See the [zero-argument setter gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/UpdateErrorZeroDoesNotClearFlag.md).

## Null atom state and actual publication

The complete `moAtom_c` serializer `[0x4bcefbb0,0x4bcf02e1)` initializes runtime `+0x160` to null before reading `body_kind`. Kind zero leaves it null for later publication, kind one loads an inline body, and kind two sign-extends an integer handle. Kind-two store requires the separate reached archive-helper `+0x874` lane. Ordinary kind zero is not by itself evidence of malformed input, and no kind change is proposed.

The complete `moAtom_c::setBody` is `[0x4bcfb360,0x4bcfb63b)`. Null body returns immediately; the normal body setter also requires a nonnull feature. After its reached native attribute and cache-map work, it publishes the actual body to `+0x160` at `0x4bcfb617` and feature to `+0x148` at `0x4bcfb61e`. Earlier feature-output selection, alternate direct stores, later clearing and the actual cold-open path are not closed here. Missing setter events do not prove absence of publication.

## Verification and next discriminator

The [source receipt](../measurements/2026/PartBodyAdmissionStateSource01.json) binds original function groups, windows, selected imports and table cells. The existing stateless verifier checks unchanged PE bytes and exact exception-directory extents, not product behavior. No native calls, tests, schema/codec execution or acceptance credit are reported.

The smallest next root-owned observation is the single comparison site `0x4c23f589`: read all raw operands and part update words, continue normally without changing target state, then record the ordinary open result. `expected > sum` identifies the exact explicit invalidate/clear branch. `expected <= sum` excludes only that branch and leaves the measured `+0xde8` need-update/error operands and earlier atom selection as the next boundaries. Warm native control is a module-loading precaution, not a claimed model remedy. All original failures and prior packets stay immutable.
