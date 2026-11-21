# Downstream ID archive grammar in SOLIDWORKS 2026

**Static direct-body grammar recovered; complete recursive stream admission and native readback remain unqualified.** This record adds field order, pointer types and archive-context rules. It does not add a decoder, writer, generated values or acceptance credit.

| Item | Scope |
| --- | --- |
| Task | B04-SW2026-DOWNSTREAM-ID-DATA |
| Owner | `/root/flag_ownership`; root owns integration, the allocator and native oracle |
| Delivery | PR #121 |
| Version | Ordinary non-DB archive, effective version 19000, not adding a configuration |
| Inputs | Original pinned licensed DLLs and the published downstream/primitive findings; no CAD payload opened |
| Exit | Bind the actual standalone archive map origin and reached class closure, then measure full byte/map/alias replay on a disclosed saved control before codec admission |

## Exact native owners

The [numeric evidence](DownstreamIdArchiveGrammar2026.json) binds three original modules, 31 complete function or leaf bounds, 32 instruction windows, eight runtime descriptors/Serialize cells and 31 selected imports. Function bounds use the declared PE exception-directory size and all chained unwind fragments. Complete small leaves stop at their actual return or tail jump; they do not include an adjacent function. No vendor instructions or decompiled listing are included.

| Owner | Original module | Complete half-open body | Bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| `moDownstreamIdData_c::Serialize` | `sldmodu.dll` | `[0x4b51fee0,0x4b522086)` | 8614 | `977c09d21a6eb6da82d60df71897d6c229edeba4126fd85f62ac1ff56e36e261` |
| `uniqueIdInfo_c::Serialize` | `sldmodu.dll` | `[0x4b522090,0x4b52216b)` | 219 | `c7ae3d1a840f7e10dfbf45cf2dba0ed8eb104a8b622c226e6779675d415338a2` |
| `moModel_c::loadDownstreamIdData` | `sldmodu.dll` | `[0x4b5860e0,0x4b5863ba)` | 730 | `5daead44f9317f6bc6b744dc288d320b2b35ed2ff2a3730891be5cc72f03d5c3` |
| Archive-helper constructor | `sldmfcu.dll` | `[0x3c7a8970,0x3c7a8e0b)` | 1179 | `5538b7e3003161ffe5aed7329c9c78d4a842fe6ba359654cf8788c1f3af19dff` |

The original model DLL SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. The helper DLL is `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`, base `0x3c720000`. The time archive DLL is `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c`, base `0x31a30000`. All match the pinned 34.5.2.0604 release manifest.

Actual primary table `0x4ce16e78+0x28` points to the downstream body. Table `0x4ce16d58+0x28` points to `uniqueIdInfo_c`. Their runtime descriptor schema words are `0x80000001`, giving ordinary wire schema 1 through the existing generic archive class rule. The downstream body calls no base serializer. A nearby LLVM export label does not identify this body; the actual table and function bounds do.

## Ordinary version-19000 field order

Every scalar below is little-endian. Runtime member names identify this class only; its `f08` is not a persistent `moNode_c` identifier.

The fixed prefix is seven u32 words, `f08,f0c,f10,f14,f18,f1c,f20`, followed by `su_CTime f28`. The first word is the previously bound shared downstream next-ID counter. The remaining counter meanings are not newly established here.

`su_CTime` has an i64 runtime member but emits one u32. Store keeps the low 32 bits; read maps `0xffffffff` to runtime `-1` and zero-extends other words. Complete `swccu` read `[0x31a4bc60,0x31a4bc9b)` and store alias `[0x31a4bcb0,0x31a4bcb7)` confirm this boundary. The prefix is **32 bytes**, not 36. See the independent [clock ownership record](DrawingSourceEpochOwnership2026.md).

Each collection has a **fixed signed 32-bit count** followed by these rows. Neither vendor variable-count nor MFC variable-count escapes apply. Vectors serialize rows in their retained order; hash-container rows use actual native iteration, not an analytic geometric sort.

| Order | Runtime member | Per-row wire fields |
| ---: | --- | --- |
| 1 | `f40` | Archive pointer constrained to `moEntityIdRep_c` |
| 2 | `f48` | Pointer constrained to `moCompFace_c`, then u32 ID |
| 3 | `f60` | Pointer constrained to `moCompEdge_c`, then u32 ID |
| 4 | `f78` | Pointer constrained to `moCompVertex_c`, then u32 ID |
| 5 | `f340` | u32 key bits; conditional `uniqueIdInfo_c` pointer below |
| 6 | `f380` | i32 key bits; conditional `uniqueIdInfo_c` pointer |
| 7 | `f3c0` | i32 key bits; conditional `uniqueIdInfo_c` pointer |
| 8 | `f540` | i32 set member |
| 9 | `f100` | i32 key, `moCompFace_c` pointer, i32 word |
| 10 | `f180` | i32 key, `moCompEdge_c` pointer, i32 word |
| 11 | `f200` | i32 key, `moCompVertex_c` pointer, i32 word |
| 12 | `f90` | `moCompSolidBody_c` pointer, i32 ID bits |
| 13 | `fa8` | `moCompSurfaceBody_c` pointer, i32 ID bits |
| 14 | `f400` | i32 key bits; conditional `uniqueIdInfo_c` pointer |
| 15 | `f440` | i32 key bits; conditional `uniqueIdInfo_c` pointer |
| 16 | `f280` | i32 key, `moCompSolidBody_c` pointer, i32 word |
| 17 | `f300` | i32 key, `moCompSurfaceBody_c` pointer, i32 word |
| Identity | `f30`, `f38` | CString UUID, then high32 and low32 of the packed owner key |
| 18 | `f650` | i32 key, then `mgPoint_c`: x/y/z as three f64 values |

The object pointers use the ordinary archive null/new-class/class-reference/object-reference grammar, with class constraints supplied to `ReadObject`/`WriteObject`. They are not native pointer bytes or fixed-size 16-byte records. The complete twelve typed pointer wrappers bind all six expected classes. The generic [tag grammar](ArchiveTagGrammar2026.md), [CString rule](CStringArchive2026.md) and [point rule](GeometryArchive2026.md) remain separate shared primitives.

Read-side loops use signed positive counts. A canonical bounded codec should reject negative or impractical counts explicitly; this report does not claim the native reader rejects every negative count. Runtime capacity, list links, hash buckets and alignment are not emitted. An all-empty-collection body has `112 + encoded_CString_length(f30)` bytes, excluding outer framing. This is a format-size formula, not an empty-state construction default.

## Unique-info framing and native normalization

`uniqueIdInfo_c` has exactly 20 body bytes: i32 `f08`, i32 `f0c`, i32 `f10`, u32 from runtime `+0x18`, then u32 from runtime `+0x14`. Those last two words are the high and low halves of the packed runtime value at `+0x14`. There is no base body or local version gate.

The five key/unique-info maps have asymmetric native conditions. Store emits the key, then an archive object only when its runtime value pointer is nonnull. Read consumes that object only when the **unsigned key is nonzero**. A canonical native store/load pair therefore needs consistent key/value presence. Do not unconditionally emit an object tag after every key. A nonzero key can consume a null archive tag on the raw read path, but native runtime reconstruction skips a null result; a later native save need not preserve that row.

Raw-wire replay must remain distinct from native reconstruction:

- `f40` creates an empty vector even for zero count and skips null object results.
- `f540` inserts into an ordered signed-integer set, sorting and deduplicating input rows.
- `f340/f380/f3c0` rebuild associations using type codes `0x138c/0x138a/0x1389`, then destroy temporary unique-info read objects.
- `f400/f440` clone unique-info values before destroying the temporary object.
- `f650` always consumes its point, including key zero, then omits a key-zero runtime insertion.
- Adding a new configuration can retarget external ownership under `f40` and clears the UUID/key; ordinary raw replay must not perform that fixup.

These facts do not admit arbitrary malformed/tombstone rows as byte-stable native round trips. [Conditional-object gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/DownstreamMapsHaveConditionalObjects.md).

## Version and context gates

The current store emits tables 9–11 unconditionally, while load reads them only from `0x3348`. Tables 12–17 are gated at `0x334a` in both branches. UUID, owner key and table 18 begin at `0x3359`. Version 19000 reaches every row above. The store/load asymmetry forbids inferring a symmetric historical writer from this current-version body.

The ordinary loader opens `Contents` and the active configuration's **actual storage name** plus `-DownstreamIdData`. It constructs a new helper with condition word zero, null context/history arguments, the actual model, and the actual file version. It sets helper `+0x8bc=1`, constructs the downstream object, and calls the object's Serialize slot at `0x4b58630f`. The exported helper getter/setter independently name `+0x8bc` as `SerializingDownstreamIdData`. The load then sets the model owner, attaches model `+0x1348`, publishes its owner key, and clears the helper flag.

There is **no outer object/class tag** or Resolved-style map-count prefix on this direct-body path. The archive belongs to the opened storage stream. Neither this caller nor the helper constructor copies a Header/Config/Resolved snapshot. The exact initial generic map state across all concrete storage `virtual+0xa0` implementations remains unproved; this record does not prescribe an initial count or seed.

The embedded Config branch is different. For outer versions from `0xc7d`, downstream enabled and helper condition `0x80`, part and assembly serializers write an i32 presence word. Store computes presence as `(model+0x1348 != NULL) && isAddingNewConfig()`. Load consumes that word, constructs the object when nonzero, and calls the same direct body at `0x4c229ca0` or `0x4b663dd0`. No outer pointer tag is added. Existing explicit SDK refusals under condition `0x80` are unchanged.

## Evidence and remaining work

Original-PE metadata, imports, descriptors and instruction bounds were checked statically. No vendor code was loaded or called. No CAD file, schema, codec, tests, VM or hidden source was executed or opened. Root reports no matching standalone stream in its bounded 64 published-example inventory or earlier disclosed child inventories; that search was not repeated or independently measured by this tranche.

The direct-body order is confirmed static knowledge. Full recursive stream admission is still unqualified: obtain a dedicated disclosed saved stream, bind its actual map origin, enumerate every reached concrete class and special helper-context branch, and verify full cursor/bytes/maps/aliases. Several expected pointer families remain outside the existing proven SDK profile. Full meanings of the initial counters and unique-info members also remain construction work. No runtime trace, fresh writer acceptance or held-out generalization is claimed.

The governing stopping conditions are: “The first is success under every criterion on this page.” and “The second is the end of the available context.” This scoped static handoff does not mark the CAD goal complete.

[Previous allocation/owner finding](DrawingDownstreamIdentity2026.md) · [Change](../../../Documentation/Changes/Solidworks/Inspection/Downstream/SolidworksDownstreamArchiveGrammar.md)
