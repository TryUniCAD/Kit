# Assembly child update and stale-reference decisions

The [native diagnostic](../measurements/2026/AssemblyRebuildProbe02.json)
reproduced a warning 32 on an ordinary one-component assembly, including a
fresh reopen after successful forced rebuilds and a successful separate save.
The rebuild cleared the in-memory flag with no feature problems. The newly
opened derivative returned `NeedsRebuild2=1`. This proves the flag can be
raised again at open; it does not identify which check raised it.

## Native predicates

Original `sldmodu.dll` build `34.5.2.0604`, preferred base `0x4b140000`,
SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
Hopper decompiled exact entries in the saved analysis database. The private
provider receipt `AssemblyUpdateNative01.json` has SHA-256
`2748102779131fa4fb6d06baacafa846c3a64c58cfd4f72468a7fe17430f7d4e`.
The ranges below were checked against original code and call operands.

| Owner | Half-open range | Code SHA-256 | Rule |
| --- | --- | --- | --- |
| `assemblyNeedsUpdate` | `[0x4b6883f0,0x4b68845c)` | `68ad5c7c0e47377073e7d7aa4ffcbb72f13b5eb4749c8d4020be766b05d7ccc1` | Walk mode 0; returns the child update result at walker `+0x108` |
| `assemblyOutOfDate` | `[0x4b6884e0,0x4b68854c)` | `5f14e5d23a01c3a6db28f0529c5e7989f75ceb1b0134514a687aafab7aaf2b28` | Walk mode 1; returns the reference staleness result at `+0x10c` |
| `assemblyNeedsUpdateOrOutOfDate` | `[0x4b688460,0x4b6884dd)` | `442e6df048f50d2616c2590962a6454eeacbf93c6f5c9cb3f146968f74b31eab` | Walk mode 2; returns either result |
| Walker constructor | `[0x4b6c3f20,0x4b6c3fd2)` | `aabb28a060f1953f090ed1d931d8bfb82095f2ed725b5906793972c11fc6da67` | Zeros the two results and temporarily selects the nonsuppressed component predicate |
| Walk entry | `[0x4b6fe0f0,0x4b6fe1df)` | `b73db05b601102d792711e81fc1b90cb3dcaa3397546ddb275eac234b6529379` | Dispatches the ordinary recursive walk through slot `+0x20` |
| Per-component handler | `[0x4b6ccd40,0x4b6ccf38)` | `5025237ab2d1445d100439f318f7e987010082255a535eb1628d6c9a2a19a6e2` | Updates the two results by distinct child and reference queries |

The ordinary recursive walk calls handler slot zero at `0x4b6fa74f`.
The walker vtable `0x4ce721e8` binds that slot to `0x4b6ccd40`. Its mode 0/2
branch resolves the child through reference slot `+0x1cc0` and queries child
slot `+0xc0`. It can also consult an external-context branch. Its mode 1/2
branch queries whether the reference is stale through slot `+0x1cd8`.
Toolbox has a separate counter comparison branch. The ordinary result uses
bit `0x20` of the query result at `+4`; that bit belongs to the native result
object and this trace has not tied it to the public load warning enum.

For ordinary reference vtable `0x4cf7a8b0`, the stale query is
`moReference_c::isModelOutOfDate` at `0x4bbc7640`. It reads the current
target header update getter, then compares reference-side update state and
tracking information. At `0x4bbc77bc` and `0x4bbc77da` it passes reference
`f3e0` to operation-kind tests for `8` and `12`. The
[insertion record](AssemblyConstruction2026.md#reference-update-state-after-insertion)
ties that reference stamp to the child's header; the configuration-local
predicate at `0x4bde3f50` instead uses its own state, including the `f0c`
mask `8` and an override at `+0x968`.

This separates persisted reference stamps, child configuration state and
local assembly rebuild state. The discovery projection records reference
stamps by archive identity alongside the assembly header counters. A causal
reopen measurement still needs to correlate the same child, ordinary
reference and configuration across save/load; no universal neutral stamp or
writer acceptance follows from these predicates.
