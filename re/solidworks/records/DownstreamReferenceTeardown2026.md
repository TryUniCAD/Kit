# Retained downstream references through ordinary teardown, SOLIDWORKS 2026

**The selected same-owner ordinary-part teardown preserves retained `f48/f60` rows and their reference fields. It does not add a cache-bit clear. This closes the two destructor boundaries left by the late-edge checkpoint, within the exact guards below; it does not qualify a native generated cache or an arbitrary later save caller.**

Task `B04-SW2026-DOWNSTREAM-REFERENCE-TEARDOWN`, owner `flag_ownership`, delivery PR #121. Root owns cache composition, native execution and publication. Dependencies are [the late-edge pass](DownstreamLateEdgePass2026.md), [identity membership](DownstreamIdentityMembership2026.md), [fresh face rows](DownstreamFreshFaceRows2026.md) and [stored face state](DownstreamStoredFaceState2026.md). Their frozen records are unchanged.

## Exact source and selected context

The [numeric ledger](DownstreamReferenceTeardown2026.json) binds 51 complete function entries, 50 unwind fragments, 11 instruction intervals, six RTTI intervals, four table cells and twelve imports across these exact AMD64 build `34.5.2.604` originals:

| Module | SHA-256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldgcu.dll` | `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594` |
| `swccu.dll` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

Complete exception-directory chained groups and reviewed leaf returns/tail jumps provide bounds. No vendor instructions, listings or images are enclosed. The unchanged [source verifier](../../tooling/sw2026/downstream/VerifyRuntimeOwnerSources.py) accepts the licensed `--bin-directory`, this numeric `--record` and an unused `--output`. The [receipt](../measurements/2026/DownstreamReferenceTeardownSource01.json) checks source custody only.

The selected conditions are the actual ordinary `moPart_c`, same-owner helper state, collision-free retained references, and successful transfer of the collector vector into downstream `f40`. Native option word zero is an explicit premise supplied by root; this lane did not inspect or attest that runtime measurement. The prior late-edge rule then excludes forced vertex/body options. Foreign helper reuse, a pre-existing different owned map, allocation failures and other model classes are outside this proof.

## The part borrows the map

Actual RTTI binds part table `0x4d1252d8` to `moPart_c`. Table slot `+0x16e0`, cell `0x4d1269b8`, reaches complete false leaf `[0x4b27cbe0,0x4b27cbe3)`.

| Source branch | Effect |
| --- | --- |
| Setup `0x4b5675d5` returns false | Select `0x4b567632`; borrow actual model `+0x1350` |
| `0x4b567640` | Write temporary owned-map flag `bb8=0` |
| Destructor `0x4b5662a1/62a8` | Skip directly to `0x4b5662de` |
| Excluded `0x4b5662c0` | No call to the model's map setter/detach |
| Excluded `0x4b5662db` | No holder virtual destructor |
| `0x4b5662e0/62e7` | Clear temporary global aliases, leaving the actual model field intact |

Complete setup is `[0x4b567590,0x4b56782a)`, SHA-256 `8f73b6b3bb0bee17412309878b910b07a641a2309dbc1c7f997de4edaf73aa45`. Complete `tempEdgeHelper` destructor is `[0x4b566270,0x4b566383)`, SHA-256 `1b5fd2a34a74c74da2e1847ae79dd4990ea30bbc736d5d643e315abd9e7a2fde`.

Setup returns early if its global holder `ba8` is already nonnull. That early return alone does not prove `bb8=0`. The preservation rule requires the analyzed setup or independently established equivalent same-owner state; it is not a claim about arbitrary nested/foreign helper ownership.

## Temporary maps destroy containers, not their pointer values

The remaining destructor cleans two actual temporary maps:

| Owner | Reached cleanup | Actual effect |
| --- | --- | --- |
| Global `0x4db57b98` | `0x4b566900`; range alternative `0x4b566630` | Both reach value cleanup `0x4b27a870`: free its own raw vector and linked nodes without an element callback |
| Same map's outer holder | `0x4b2e2ce0 ->0x4b2e3210` | Free bucket/list allocations; nested values use that same raw cleanup |
| Global `0x4db57ba0` | `0x4b2de920` | Nested values use `0x4b2af2b0`, another raw vector/list cleanup |
| Its outer holder | `0x4b2dc650 ->0x4b2dc850` | Same raw value cleanup and owned container storage release |

All complete bodies and their recursive/range helper targets are pinned. These routines do not dispatch a destructor, release method, cache clear or setter on the objects whose pointer values occur inside the containers. The nearest exported LLVM labels are not their semantic identities. [Borrowed-map gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/BorrowedSurfaceMapsKeepTheirReferences.md)

## The transferred representation vector survives

Collector transfer `[0x4b519e80,0x4b519e96)` moves its actual `+0x1b0` vector pointer into downstream `f40`, then nulls the old collector field. In derived destructor `[0x4b516eb0,0x4b517008)`, that null is tested at `0x4b516ed9..6ee3`.

The virtual `+0xb8` call at `0x4b516f00` would release original entity-ID representations if that vector remained owned by the collector. Successful transfer skips the entire loop. No clone, FR keeper or external-file/configuration owner from the transferred vector is released here.

Other derived members at `+0x130/+0x170/+0x1c0/+0x1d0/+0x210` use pinned raw nested map/tree/list cleanup. None invokes a retained BEnt or modeled-object element callback. The actual base tail jump is `0x4b516ffc ->0x4b5115d0`.

## The base owns separate comparison keys

Base destructor `[0x4b5115d0,0x4b5118e6)`, 790 bytes, SHA-256 `907c87b5033df894433881137a2844363b89b98f3db7d6f4c96f4f3eaea504fb`, frees the key tree at global `0x4db56280` and its own member containers. Tree-node cleanup does not destroy pointed-to model objects.

Its `+0x10` vector owns unique comparison-key objects. The actual producer allocates 40 bytes at `0x4b51419f`, calls imported `sldgcu!gcEntityIdDataStruct_c` constructor at `0x4b5141b5`, and retains a new key in that vector at `0x4b5142bf`. This is separate from the `f40` representation vector and the retained component/BEnt graph.

The concrete constructor installs table `0x43f693a8`; exact RTTI names `gcEntityIdDataStruct_c`. Slot zero reaches deleting destructor `[0x43882f60,0x4388301c)`, SHA-256 `14758d0e99f8f6c20444f520df6bf859388ccf206588b3b62df49616359f1931`. The base caller supplies `EDX=1`, selecting its scalar branch.

That branch releases the key's own `+0x08` integer buffer and `+0x18` object-pointer buffer, then the key allocation. It never iterates or releases the external objects held in the pointer buffer. The ordinary cap/side key callbacks independently allocate those buffers; they do not alias a retained BEnt's inline entity array or replace the concrete key vtable. Raw key storage and the objects named by a key remain distinct owners.

## Common base and allocation boundary

`swccu!su_CObject::~su_CObject`, `[0x31a3ecc0,0x31a3ed29)`, SHA-256 `41de259db5cd3bcde371902049589619ffd0ad7f110fb7123dc5633ebeb7a2f0`, is not empty. It overwrites the dying helper's vtable and performs locked process-global map bookkeeping with constant key/value inputs. It does not retain the incoming object pointer for graph traversal or receive a retained BEnt/FR owner. No semantic callback is invoked by that body.

Application-side memory release is bound to exact thunk/import identities, including MFC ordinals `266/1491` and CRT `free`. Effective ARM64X MFC allocator bodies are not newly rebound here. The source proof stops at these ordinary allocation/deallocation ABI endpoints; no retained modeled object is passed to them. It does not claim arbitrary heap instrumentation behavior.

## Retained result and remaining scope

At the completion of these selected destructors:

- Downstream `f48/f60` row pointers and allocated ID words retain their incoming values
- Component reference pointers, BEnt `fe8/f70/f18`, endpoint words and semantic operand aliases are unchanged
- The model retains its borrowed `+0x1350` map, and downstream `f40` retains the transferred vector
- No new `clearEntCache`, runtime reset, synthesized vertex hint or field-word normalization occurs

This extends the prior late-stage preservation through the requested helper/collector teardown. It does not derive the incoming state, prove validator noncollision, admit owned/foreign map branches, or qualify unrelated later incremental-update/save callers. It supplies no new native load, edit/save/reopen, held-out result or public writer admission.

No CAD payload, hidden input, VM, application, schema, codec or test was opened or executed. No shared checkout or Git state was modified. Native acceptance remains root-owned. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), [full RE playbook](../../Playbook/README.md) and [loader chapter](../../Playbook/LoaderAnalysis.md) remain authoritative. “The first is success under every criterion on this page.” “The second is the end of the available context.” This is a source checkpoint, not conversion completion.
