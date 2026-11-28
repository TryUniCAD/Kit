# Ordinary downstream entity-reference wire bodies, SOLIDWORKS 2026

Exact-build source binds the ordinary `moFaceRef_c` body reached from component and atom records, plus the direct BEnt reference body. The direct body has its own context rules. The source verification ran zero SDK or vendor processes.

Task `PR121-DownstreamEntityReferenceWire`, owner `configuration_header`, delivery PR #121. Dependencies are [the downstream archive grammar](DownstreamIdArchiveGrammar2026.md) and [the component body checkpoint](DownstreamComponentWire2026.md). The bounded exit is exact-build field/mode rules with reproducible source pins. Dynamic ID-representation closure, semantic construction and native acceptance remain work.

## Authorities and reproducibility

The [numeric source ledger](DownstreamEntityReferenceWire2026.json) binds four original modules, 35 complete function entries, six runtime descriptors and Serialize cells, four auxiliary descriptors, and 32 selected typed imports. There are 53 verified byte intervals. PE unwind chains supply complete noncontiguous bounds. The four small leaves stop at their actual return or tail jump. Incomplete 32-byte entry samples were excluded. No vendor instructions, native payloads or decompiled listing are published.

Primary authority: `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. The ledger also pins exact `sldmfcu`, `sldmgu` and `swccu` dependencies. Addresses below are preferred VAs in those exact images.

The [metadata-only verification receipt](../measurements/2026/DownstreamEntityReferenceSource01.json) verifies all original-module/interval hashes and three materialized SDK source hashes. This is not an SDK integration or vendor measurement. The [verifier](../../tooling/sw2026/downstream/VerifyEntityReferenceWire.py) reads licensed originals as bytes without loading them as code. It accepts `--bin-directory`, `--record`, an unused `--output` and optional `--checkout`. A changed checkout can still verify original pins by omitting the optional textual-source check, but cannot claim the earlier materialized source identity.

## Class dispatch and common context

| Actual class | Runtime descriptor | Serialize slot target | Body |
| --- | --- | --- | --- |
| `moBEntRef_c` | `0x4cf68698` | `0x4bba3780` | Common direct reference |
| `moFaceRef_c` | `0x4dadd6f0` | `0x4bba9640` | BEnt, then conditional face-match array |
| `moEdgeRef_c` | `0x4dadd3c0` | `0x4bba3780` | Exact BEnt reuse |
| `moVertexRef_c` | `0x4dadd810` | `0x4bbaa810` | BEnt, optional point, drawing-only words |
| `moEntityId_c` | `0x4dadcc70` | `0x4bba8bc0` | Typed representation pointer |
| `moEntRefDownstreamIdData_c` | `0x4dac4450` | `0x4b53b0b0` | Embedded map/vector/scalars |

The concrete classes have schema `0x80000001`. The abstract BEnt descriptor has `0xffff` with a null factory. Face/edge/vertex base getters return the actual BEnt descriptor. Do not substitute a stale class map or the nearest LLVM symbol label.

The scoped body is effective version 19000, non-DB, with the archive helper's `+0x48` restoration context absent. If helper model `+0x30` exists, BEnt validates it as `moFiledConcept_c` at `0x4bba37ca`. A wrong kind reaches the error tail at `0x4bba41b2`. Its `su_CObject::Serialize` base call emits no ordinary bytes when archive bit `0x10` is clear. DB mode remains separate.

The direct BEnt body does not branch on the component helper `+0x8bc` downstream flag. It does independently branch on helper `+0x48` for each entity ID at `0x4bba3c8b`. That branch calls `0x4bbac610`, rather than the ordinary inline Serialize dispatch, and remains unqualified.

## Common BEnt wire order

| Order | Owner | Current wire representation |
| --- | --- | --- |
| 1–5 | `f60`, `f64`, `f08`, `fe8`, `f70` | u32, u32, u32 count, i32, u32 |
| 6–7 | `f28`, `f30` | two f64 values |
| 8 | `f40` | nullable typed archive `moVertexRef_c` pointer |
| 9 | `f10` | `f08` inline `moEntityId_c` bodies |
| 10 | `f48` | u32 |
| 11–12 | `nd0`, `fd0` | i32 count, then pairs of `su_CTime` words |
| 13–14 | `fec`, `has_f18` | two i32 values |
| 15 | `f18` | direct embedded downstream body if presence is nonzero |

There are 52 fixed scalar bytes, plus the typed `f40` pointer, inline ID bodies, `8*nd0` time bytes, and optional embedded body. Native's entity loop is signed-positive despite its u32 count. New generation should admit only safe nonnegative counts within `INT32_MAX`, with actual row counts matching.

An inline entity wrapper is not a separately framed object. Its `f08` *is* a typed `moEntityIdRep_c` pointer, so that representation participates in the archive map normally. The `f18` downstream wrapper is also embedded: its runtime owner backlink is not serialized and no extra object/class tag belongs before its body.

`f70` is stored from its low u32 and zero-extended into the runtime qword. For the face case, [the separately bound resolver](ConcentricFaceTagAndExtent2026.md) makes it a resolved `gcFace_w` handle cache, not a permanent node, downstream ID, body atom or transmitted index. This checkpoint does not derive fresh usable handles.

Each time pair occupies eight wire bytes but sixteen runtime bytes. `swccu` stores the low u32 of each `su_CTime`. Load maps `0xffffffff` to runtime `-1` and zero-extends other words. Runtime structure size is not a wire length.

## Face suffix and typed representation restriction

Face Serialize calls BEnt at `0x4bba9669`. `hasCondition(0x80)` at `0x4bba9685`/`0x4bba9700` selects the suffix:

- If condition bit `0x80` is clear, write i32 count followed by that many inline multi-match rows
- If bit `0x80` is set, omit the count and every row

A row is exactly `i32 f08, u32 f0c, u32 f10, i32 f14`: sixteen wire bytes, no object tags. Store/load callees are `0x4b75baa0`/`0x4b75af80`. Native allocates 24 runtime bytes for each row. Nonempty row identity assignment requires further source evidence.

At version 19000, EntityId load uses the `moEntityIdRep_c` descriptor `0x4dadce80`. After read, it explicitly rejects a nonnull `moByEdgeSurfIdRep_c` at `0x4bba8da9` → error `0x4bba8db6`. A broad materialized kind list containing that class is not evidence that this ordinary load context permits it. This tranche did not execute or expand that guard.

## Embedded downstream body

`moEntRefDownstreamIdData_c::Serialize` (`0x4b53b0b0`) does not call a base serializer. Current wire order is:

1. i32 `n10`, then `n10` pairs of signed i32 key/value
2. i32 `n20`, then `n20` signed i32 values
3. i32 `f38`
4. i32 `f40_0`, i32 `f40_1`

Its size is `20 + 8*n10 + 4*n20`. The native map store walks the signed-key tree in order. Load clears/reconstructs it and overwrites duplicate-key values. Vector load consumes every wire row but does not append zeros (`0x4b53b3a5/0x4b53b3a7`). A raw codec must retain row order, duplicates and zero values rather than perform those native fixups during byte retention. See [the specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/EntityReferenceRowsNormalizeOnLoad.md).

The two trailing words have proved width and order, but their full model meaning and nondefault generation are not established. No UUID/hash packing rule is inferred from neighboring classes.

## Vertex suffix and identity domain

The ordinary part suffix is i32 presence followed, when nonzero, by three inline f64 point coordinates. Its store/load calls `sldmgu` point operators at `0x31f09060`/`0x31f09020`, which use three successive double primitives.

An actual drawing helper model appends four i32 words `ff8, ffc, f100, f104`. Outside detailing mode, when a cached valid vertex has incident edges, the store obtains the first incident edge (`0x4bbaa903`/`0x4bbaa91f`), reads that edge's `gcEnt_w::getNodeId` at `0x4bbaa942`, and passes it to index 3 of setter `0x4b759b00`. Therefore `f104` receives an **incident edge's node ID**, not the vertex node ID. The preceding downstream-attribute getter's return is not the setter argument.

Incident-edge ordering is not established by this path. Do not infer first fin, minimum tag, transmit order or body traversal order. The other three drawing identity words also require owner rules before generation. See [the vertex-specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/VertexReferenceSuffixUsesIncidentEdge.md).

## Fresh defaults, normalization and materialized reuse

The native BEnt default constructor sets the two identity words `f60/f64` to `0xffffffff`, optional owners/counts to zero/null, `f28=f30=1e100`, `fe8=0`, and `f70=0`. `fec` comes from the version manager's current-file-version getter, not a document capture. Face adds null match-array ownership. Vertex adds null point, zero four drawing words and zero nonwire cached vertex. A new match row starts `(0,0,0,-1)`. The downstream wrapper starts with empty map/vector, `f38=0`, and both trailing words zero.

These are constructor states, not oracle-proven usable references. Current native BEnt load also clears `f64` when `f60==1`, repairs face/edge/loop sentinel identities to `(1,0)`, and can add loop flag `0x2000`. Raw retention and native reconstructed state must remain distinct.

The ledger pins the exact three source files at audit head `afa1380c00c8cc8b8c3e5e34100f79276ee40173`. `ReferenceFields.py` already materializes the common order, face mode and inline EntityId grammar. Four literal owner bodies were absent in that snapshot: edge alias, vertex suffix, embedded downstream body, and four-word match row. Reuse the existing field executor and materialized reference bodies rather than duplicate them. Keep helper `+0x48`, DB mode, unknown ID representations and historical versions explicit refusals. The numeric record retains the historical read gates. Earlier writer versions need separate evidence.

The next proof is root-owned typed process replay over complete downstream graphs and disclosed payloads, followed by a controlled native load/rebuild/save batch for any generated identity semantics. No production registration or writer admission is established here.
