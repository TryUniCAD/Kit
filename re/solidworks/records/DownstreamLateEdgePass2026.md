# Selected downstream late-edge and vertex pass, SOLIDWORKS 2026

**The selected fresh mode-1 prism pass performs no late vertex work when the actual pending tree is empty and native option bit 0 is clear. This is a source-only checkpoint; final cache save readiness and CAD acceptance remain unqualified.**

Task `B04-SW2026-DOWNSTREAM-LATE-EDGE-PASS`, owner `flag_ownership`, delivery PR #121. Root owns edge operands, cache composition, native execution and publication. The configuration lane owns [initial and post-insert validation](DownstreamEdgeValidation2026.md). This tranche changes no codec, builder or production source. Its exit is replayable exact-build late-stage rules with the remaining teardown/store boundary retained.

## Source custody

The [numeric ledger](DownstreamLateEdgePass2026.json) binds 31 complete function entries, 32 chained unwind fragments, 27 instruction intervals, four data intervals, six virtual cells and ten imports. Original `sldmodu.dll` is build `34.5.2.604`, AMD64, preferred base `0x4b140000`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Bounds use the declared exception directory and complete chained groups; four small leaves stop at reviewed returns. Original instructions and vendor software remain external and are not distributed.

[Source replay](../measurements/2026/DownstreamLateEdgeSource01.json) uses the unchanged [metadata verifier](../../tooling/sw2026/downstream/VerifyRuntimeOwnerSources.py). Invoke it with the licensed original `--bin-directory`, this numeric `--record`, and an unused `--output`. It reads original PE bytes without invoking them. The receipt does not establish SDK, native, malformed-input or held-out acceptance.

The preceding assignment, validation, wire and membership JSON records are hash-bound dependencies. They are not modified. This lane opened no CAD input, held-out, VM, persistent REA/Hopper target or application process and ran no test, schema or codec.

## Actual order

`moModel_c::createDownstreamIdData`, `[0x4b578680,0x4b5788a5)`, calls the fresh orchestrator at `0x4b578824`. The orchestrator `[0x4b5263c0,0x4b52696f)` has this order:

| Call site | Target | Selected role |
| --- | --- | --- |
| `0x4b526500` | `0x4b52b130` | Face rows |
| `0x4b526568` | `0x4b52ab60` | Edge rows |
| `0x4b526626` | `0x4b52b640` | Conditional all-body vertex rows |
| `0x4b52662e` | `0x4b5360d0` | Pending-edge late repair |
| `0x4b526823` | `0x4b525b90` | Conditional temporary curve cleanup |
| `0x4b52682d` | `0x4b566270` | Temporary helper teardown |

`0x4b525b90` is not the late repair caller. It walks the temporary curve list at data `+0xb48/+0xb50`, destroys nonnull actual curves, then clears that list. Reading its nearest LLVM symbol as its identity would give the wrong role.

## Fresh pending state and selected mode

The complete downstream constructor `[0x4b51d470,0x4b51d979)` initializes an empty native tree at `data+0xb38`, with count `data+0xb40=0`. The tree key is the actual BEnt pointer. Values retain a selected actual endpoint vertex and an actual coedge, rather than wire row IDs.

Inserter `[0x4b527670,0x4b527786)` can add or update that entry. An entire original file-backed `.text` E8-rel32 scan finds one direct candidate, `0x4b75ae3d`; complete owning decode confirms the call instruction and its target. This does not exclude arbitrary indirect or inlined writers globally.

The actual initial CompEdge call passes mode 1 at `0x4b52ad34..0x4b52ad48`. In semantic edge initializer `[0x4b75a880,0x4b75af73)`, nonzero mode selects `0x4b75ac71`: publish qword 1 at `BEnt+0x60`, bind actual body/coedge through `0x4b759590`, then jump at `0x4b75ac94` directly to the return tail. The later candidate-search/pending-insert/vertex-hint branch is not reached.

The initial retry and post-replacement collector calls at `0x4b52ad87` and `0x4b52b038` reach the erase helper `0x4b5279a0`; they do not insert. Root's independently bound unchanged-validator conditions exclude those retries. The initial common-edge test and absence of both original and applicable anti keys remain mandatory inputs to this selected path. Rectangle geometry alone is insufficient.

## Exact vertex predicate

At `0x4b5265b6`, the orchestrator reads native option word `0x4db5681c`. It selects the all-body vertex collector if bit 0 is set. Otherwise a nonzero pending count selects that collector only when it exceeds `0.25 * signed_i32(data+0xbdc)`. The exact f64 multiplier is at `0x4cde9a80`.

When neither condition selects all-body collection, the fallback at `0x4b52684a` wraps and appends only actual endpoints from the pending tree. A zero pending count skips that fallback too. The complete original direct-call inventory for vertex appender `0x4b5250e0` has exactly two decoded sites:

| Call site | Owner | When reached |
| --- | --- | --- |
| `0x4b526902` | Fresh orchestrator | Nonempty pending-only fallback |
| `0x4b52b86c` | All-body vertex collector | All-body branch selected |

Consequently a fresh vertex vector `f78` remains empty through the selected late-stage return when pending count is zero and bit 0 is clear. A generator must establish those predicates rather than infer an empty vector from a saved row.

The all-body branch is not an ambiguity-only filter. It collects actual body vertices, preserves returned native order, constructs aligned nullable VertexRefs, chooses actual body component or self component, copies actual body atom into wrapper `f18/f1c`, and appends rows. The selected zero-pending path does not need those allocations. General vertex collision/disambiguation semantics remain outside this checkpoint.

## Late repair and the two endpoint words

Complete late repair `[0x4b5360d0,0x4b53658e)`, 1,214 bytes, SHA-256 `46ce229823919fb271a94e8ebd3b825dd151294c84b93540b5c07cc177e5a1e5`, spans five chained unwind fragments. It first checks `b40`; zero returns at `0x4b5360e4` before touching any retained reference.

For nonzero pending state it also requires an actual part, actual reference virtual `+0xf8` true, null BEnt `f40`, and a valid selected endpoint's `f78` row index. Exact concrete tables return true for EdgeRef and false for FaceRef/VertexRef at that slot.

The reached per-entry path copies the actual VertexRef, clears/resets the edge runtime cache, tries to install the copied vertex hint and checks the actual coedge resolution. The hint helper can reject a mismatch and clear the hint. If embedded `BEnt.f18` exists, setter `[0x4b53b6f0,0x4b53b6ff)` writes its two trailing words: selected pending vertex-row ID first, opposite actual edge endpoint's vertex-row ID second, or zero when that other row is absent. It uses actual edge start/end accessors to find the opposite endpoint. These are neither face IDs nor unconditional geometric start/end ordering.

| Owner | Selected zero-pending result at return to `0x4b526633` |
| --- | --- |
| `data.b40` | Remains zero |
| `data.f78` | Fresh empty vector, no vertex row allocation |
| `BEnt.f40` | Unchanged; null in selected fresh mode-1 construction |
| `BEnt.f18.f40_0/f40_1` | Unchanged constructor zeros |
| `BEnt.fe8` | Unchanged incoming mode-1 bits |
| `BEnt.f70` | Unchanged incoming value |

The embedded owner and its role map remain present. Skipping late endpoint repair does not justify removing `f18` or its existing face-role rows.

## Cache flags and wire state

`0x4b759590` masks `fe8` by `~0x700` while clearing runtime cache owners, then publishes branch-specific cache bits. Its selected ordinary body, nonnull coedge and Boolean 1 path contributes `0x100|0x200`. It does not write `BEnt.f70`, the embedded `f18`, or `f60/f64`.

`clearEntCache`, `[0x4b74c510,0x4b74c56b)`, also clears runtime cache owners and masks `fe8` by `~0x700`; it likewise leaves those wire owners intact. The selected zero-pending late pass does not call it. [Cache-flag gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/Edges/EdgeCacheBitsAreSerialized.md)

Actual EdgeRef table `0x4ce862e0+0x28` dispatches directly to BEnt Serialize `0x4bba3780`. In the ordinary store branch, the code loads `fe8` at `0x4bba3843` and writes it verbatim as i32 at `0x4bba384c`. It loads the low 32 bits of `f70` at `0x4bba3852` and writes u32 at `0x4bba3858`. There is no implicit serializer `0x700` mask. Component `+0xe8` is its actual reference pointer; it is a different owner from that pointed-to BEnt's scalar `fe8`.

Thus an independently proven incoming `fe8=0x300,f70=0` survives the selected late stage. This is not a universal saved-word default or proof of preservation through every later owner. The serializer rule says what it writes from the state that reaches it.

## What this closes and what remains

For the bounded collision-free mode-1 prism, no vertex rows, synthetic hint or endpoint-word repair is required by this late stage. Carry actual incoming flags and handles rather than inventing a post-validation clear. Initial reference construction, body atom, shared row allocation and validator predicates remain independently owned dependencies.

Fresh create scope exit `[0x4b51f880,0x4b51f88c)` only clears global `0x4db5dd20`. Collector transfer `[0x4b519e80,0x4b519e96)` moves its actual `+0x1b0` vector to downstream `f40` and nulls that collector pointer, excluding the matching vector-release loop on successful transfer. It does not prove that all other teardown callbacks are harmless.

The exact remaining lifecycle boundary includes temporary-helper model partition detachment at `0x4b5662c0`, holder virtual destruction at `0x4b5662db`, nested cache/representation cleanup at `0x4b5662fa`, and collector-base teardown reached at `0x4b516ffb`. Their transitive effects on retained references are not closed here. Later incremental update, actual selected save, forced vertex mode, collisions, assemblies and wider kernel contexts are also unqualified. Root must retain these boundaries before claiming complete `f60` cache readiness or native save acceptance.

The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), [full RE playbook](../../Playbook/README.md) and [loader phase](../../Playbook/LoaderAnalysis.md) govern the work. Their stopping conditions are: “The first is success under every criterion on this page.” “The second is the end of the available context.” This is a bounded source handoff, not conversion completion.
