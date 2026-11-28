# Ordinary drawing edge references in SOLIDWORKS 2026

This is a bounded raw-wire reader tranche. It does not qualify the original drawing writer, public drawing semantics, native output, or the complete original Definition streams. The earlier two original rejections remain in custody. The exact frozen executable source passed an independent 43-worker prior-profile replay. Both actual originals still fail closed in their first edge body at the next concrete `moFromSktEntSurfIdRep_c` schema-one dependency.

Task: PR121 drawing Definition edge-reference dependency. Owner: `flag_ownership`; delivery PR: #121. Dependencies: the integrated component-profile and reference-chain readers. Exit for this tranche: an independently reviewed ordinary-19000 concrete edge/base layout, the optional downstream helper grammar, exact source custody, and a retained real parser result or next explicit boundary. Full CAD acceptance remains separate.

## Native identity

All addresses refer to the licensed SOLIDWORKS `34.5.2.0604` originals. The [machine-readable proof](DrawingEdgeReferenceArchive2026.json) records module identities, actual vtables/descriptors, complete exception-directory fragment closures, and original-byte hashes. No native application or vendor code was executed by this worker.

| Module | SHA-256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `slduiu.dll` | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| `doccplu.dll` | `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8` |
| `slddrwu.dll` | `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47` |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `swccu.dll` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

The actual `moEdgeRef_c` primary table `0x4ce862e0` has serializer slot `+0x28` equal to `0x4bba3780`, the same target as `moBEntRef_c` table `0x4ce86190`. Edge RTTI derives from `moBEntRef_c`, `su_CObject`, and `CObject`. Its descriptor uses versioned schema `0x80000001`, so concrete wire schema is one. The base descriptor is `0xffff`; it is not a new concrete schema-one class.

The complete shared serializer is `[0x4bba3780,0x4bba41ef)`, 2,671 bytes, SHA-256 `e5491d90050bf64fd704e55ddf869319cc680b69a3a3559bb7e3d8827ff90c07`. There is no edge subclass suffix.

## Current wire order

The table describes the ordinary non-database version-19000 branch only. These are input wire values; this tranche supplies no fresh constructor values or semantic defaults.

| Order | Field | Encoding and rule |
| ---: | --- | --- |
| 1 | `f60`, `f64`, `f08` | Three `u32` words |
| 2 | `fe8` | `i32`, present since `0x20c` |
| 3 | `f70` | `u32`, present after `0x496` |
| 4 | `f28`, `f30`, `f40` | Two `f64` values and a typed vertex-reference object, after `0xa04` |
| 5 | `f10` | `signed-positive-low32(f08)` embedded `moEntityId_c` records |
| 6 | `f48` | `u32`, after `0x536`; the obsolete extra ID array exists only before `0x542` |
| 7 | `nd0`, `fd0` | `i32` count then `max(nd0,0)` pairs of raw `u32` time words, after `0x23bb` |
| 8 | `fec`, `has_f18` | Two `i32` words, after `0x332c` |
| 9 | `f18` | Embedded downstream data exactly when `has_f18 != 0` |

The complete ordinary entity-ID serializer is `[0x4bba8bc0,0x4bba8ddc)`, 540 bytes, SHA-256 `d2978a6ce7c634f5615f7d471d08f6ce558ff4b7785259df9a3dc2775c098bf5`. Its actual table slot is bound in the proof. Reachable concrete ID representations still require their own existing schema and type admission; the edge alias grants no bypass.

The native loader repairs `f64` when `f60==1`, repairs selected edge/face/loop sentinel words, and clears runtime caches. The generic codec retains the original wire words. Applying those native runtime repairs to a raw replay would change the document encoding.

## Actual helper owner

The relevant constructor is a separate UI-layer overload. `doccplu!SolidStorage_c::LoadDefinition` at `0x1800248e0` opens `Contents/Definition` and calls the constructor at `0x180024ac4`. The actual path is thunk `0x180046731`, IAT `0x180053510`, then exported `slduiu!moArchiveHelperObject_c(su_CArchive*,SldModelContext_c*)` at `0x496f5680`.

That complete constructor is `[0x496f5680,0x496f5eac)`, 2,092 bytes, SHA-256 `82386034628af145501c498f14cb7ab2a7287acf2e2f8ab6afa2edd6f8d2cb34`. It clears `helper+0x48` at `0x496f56ca`, with the zero source bound at `0x496f56a6`. It registers the actual supplied archive/helper association at `0x496f5d32`. This is direct cold constructor evidence, not a constant fitted to an original file.

`LoadDefinition` uses a fresh helper at stack `+0x50`. Its direct writes before the document call set the file version and an existing drawing flag. They do not set `helper+0x48`. At `0x180024b1e` the real document `+0x1008` call reaches `uiDrawingDoc_c::Serialize`, actual table `0x3e1d6b78`, target `0x3debc450`; the common UI serializer is `0x497011e0`.

The drawing model's `0x4c224e10` dispatch selects the two modern virtuals `+0x4b8` and `+0x4c0` at versions at least `0xc7d`. For the actual drawing table those resolve to `0x4c22ec80` and `0x4c234150`. The large legacy body is excluded at 19000. No direct helper+48 access was found in those bounded modern bodies or the drawing root; this bounded search is not proof of every transitive callback's preservation. Native edge-time state has not been observed.

The nonzero-helper alternative is materially different: `[0x4bbac610,0x4bbac839)`, 553 bytes, SHA-256 `0662dd41fcb2093078fdff3d49985aeb97db4eb201fd1e0538a5262eddd87976`, reads a byte presence, uses MFC runtime-class loading, and calls virtual `+0x118`. It is not an ordinary object-tag serializer. The SDK retains a closed failure for this mode.

## Downstream helper

The actual `moEntRefDownstreamIdData_c` table is `0x4ce17298`; slot `+0x28` reaches `0x4b53b0b0`. RTTI has the direct `su_CObject` parent, not a guessed downstream base. Descriptor `0x4dac4450` has schema `0x80000001` and size 112. The constructor `[0x4b53ad00,0x4b53adce)` installs that actual table; the owner pointer is runtime state, not a serialized extra field.

The complete serializer `[0x4b53b0b0,0x4b53b46b)` is 955 bytes, SHA-256 `573f99c70616689d1cbafbf603ae99a1ada31a168f5342aaae3a2b7cbf271ba5`. It makes no own base-serializer call. Its ordinary wire order is:

1. `n10:i32`, then `max(n10,0)` rows `key:i32,value:i32`
2. `n20:i32`, then `max(n20,0)` rows `v:i32`
3. `f38:i32`
4. `f40_0:i32,f40_1:i32` for versions at least `0x3359`, with no extra length prefix

Native map loading overwrites duplicate keys; native map storing traverses signed keys in order. The vector loader drops zero entries. The raw codec preserves row order, duplicate rows, zero words, and the on-wire counts through the shared typed count mechanism. It does not claim that every noncanonical raw encoding is a native store fixed point.

## SDK boundary and evidence

The private candidate adds one concrete drawing schema and two small field modules. The existing shared `moBEntRef_c` field sequence remains unchanged. The drawing alias requires the existing ordinary drawing/FRData guard and zero `ctx48`. The helper is embedded, so no standalone concrete schema admission is added for it. The global SDK layout entry still requires version 19000; parts, assemblies, early versions, database streams, and special contexts are unchanged.

AST, Black, Ruff, strict Mypy, strict Pyright, steering, and the recorded-payload static scan pass for the four SDK paths. Candidate01's two punctuation-only rationale findings are retained; Candidate02 differs only in those comments. No worker test suite, native execution, VM call, Git action, original writer change, or held-out acceptance is included.

[Reader custody and current results](../measurements/2026/DrawingEdgeReferenceReader01.json) retains the original two schema rejections. The new source manifest has 4,350 files. Root independently passed all 43 prior-profile workers on Candidate02. Candidate04 corrects only native read/store evidence labels and manifest metadata; all 4,350 executable/dependency file records are literally identical. Both actual originals advance from the former `moEdgeRef_c` class rejection into that body, then reject `moFromSktEntSurfIdRep_c` schema one at cursor 31,636 and 31,632. The edge body itself is incomplete and the populated downstream branch has not been reached. The exact probe source/inputs remained immutable; full Definition parity remains false. The prior metadata is retained.

Confidence: concrete native identity and selected raw field order are confirmed static facts; cold constructor ownership is confirmed; transitive helper preservation at the actual edge and semantic construction are partial/unmeasured. Complete drawing parity and native acceptance are not inferred.

The governing stopping conditions remain exact: “The first is success under every criterion on this page.” and “The second is the end of the available context.” Missing grammar remains work.
