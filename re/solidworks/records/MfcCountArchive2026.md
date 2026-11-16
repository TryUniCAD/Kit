# Framework count and string-to-int map in SOLIDWORKS 2026

The complete reached framework count bodies and their effective mapped bytes are bound to the pinned runtime. The ordinary-version-19000 `su_CMapStringToInt` owner can therefore use a separate, independently authored MFC count operation. New archive replays, strict source admission and fresh writer acceptance remain pending. No count method or CAD application ran in this investigation.

## Scope and field ownership

[MfcMaps.py](../../tooling/sw2026/serial/defs/MfcMaps.py) defines the direct embedded owner `su_CMapStringToInt`. It preserves the pre-existing keys and row order:

| Order | Key | Encoding | Ownership |
| --- | --- | --- | --- |
| 1 | `n` | Framework count, unsigned domain through 64 bits | Native map entry count at runtime `+0x18`; explicit decoded count, with no default |
| 2 | `items` | Exactly `n` rows | Existing ordered row representation |
| 2a per row | `k` | Existing shared CString operation | Native string-key boundary |
| 2b per row | `v` | i32 | One four-byte integer value |

The ordinary CMgr schema reaches this map as embedded `f600` when document version is greater than `0x12de`; that gate is active at 19000. The map helper is a direct exported serializer, not a separately tagged class in [SerializeMap2026.json](../../data/Serialization/SerializeMap2026.json). No class tag, base payload or extra framing is added. Existing CString encodings and row values remain with their existing owners.

The new owner is discovered by the existing sorted definitions loader. `MfcMaps` sorts before `SmallCMgr`; the latter's retained provisional declaration cannot override an existing definition. Registry promotion is a bounded field-order assertion, not a native model acceptance claim. The helper is under `defs/`, so existing FieldScan implementation fingerprints include it without a new top-level provenance exception.

## Exact native module and dispatch binding

Addresses below refer only to these private images. Vendor images, captured instruction bytes and proprietary listings remain outside checkouts.

| Image | Preferred base | SHA-256 |
| --- | --- | --- |
| `swccu.dll` | `0x31a30000` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |
| System32 `mfc140u.dll`, version `14.50.35719.0`, 12118600 file bytes | `0x180000000` | `88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1` |

| Native owner | Complete half-open span | Span SHA-256 |
| --- | --- | --- |
| String-map exported leaf | `[0x31a376c0,0x31a376cb)` | `452ce506aa518b89cd2025a3dde69b33686ceb6cad73be18b05e892aac32deb7` |
| String-map ordinary tail target | `[0x31a37540,0x31a37689)` | `2c4cfb0e3304b3d6169ae77815d8c1aea36b1e5cf76eae473b81945e871c5635` |
| Integer-element helper, all six chained fragments | `[0x31a31720,0x31a317fd)` | `a3381c4f01c65578b521d5a350249340ddb425a63ce979aed6a6181481d2b130` |
| Framework ReadCount, ARM64EC | `[0x180557b30,0x180557c50)` | `cd381ab524f765a17274de09b371c47ed028f0c3b2b31804eb3871fa71a5c0e4` |
| Framework WriteCount, ARM64EC | `[0x180557980,0x180557b28)` | `ad9500fd35f8e392d159dbebacd41f377ec1fdbf9f778a25c76c2834af7fda84` |

The exported map leaf tests native archive flag `0x10` at archive `+0x20`. If set, it returns without a payload; otherwise it tail-calls the ordinary implementation. That implementation selects load when mode bit `0x1` is set, and store when clear. It has no document-version comparison. Native store obtains its count and traverses its buckets, emitting a CString followed by one integer for each row. Native load reads the count and then those rows. The integer helper transfers `4*element_count` bytes, chunked at `0x1fffffff` elements; this caller passes exactly one. Short reads and a positive count with a null data pointer enter separate failure paths. There is no additional integer framing.

The framework read import is `swccu` thunk `0x31a4c719`, IAT `0x31a502f8`, `mfc140u.dll` ordinal `12087`. The write import is thunk `0x31a4c71f`, IAT `0x31a502f0`, ordinal `14278`. These are distinct from the vendor count functions in the next section.

The raw file has ARM64X machine `0xaa64`. Its unmodified export table gives different ordinal addresses, so reading that table alone does not bind the effective x64 import. The measured AMD64-facing module has an effective PE machine of `0x8664`, image size `12181504` and mapped base `0x7ff8442d0000`. Both GetProcAddress results equal their effective mapped export-table entries. The reached targets are established by exact fourteen-byte x64 fast-forward thunks:

| Ordinal / role | Effective export RVA | Complete thunk SHA-256 | Target RVA | Complete body bytes |
| --- | --- | --- | --- | ---: |
| 12087 / read | `0x6bcc70` | `fa55fff220c458e914d00249b5fb46b623778bdde557fe261afeb6883fee0469` | `0x557b30` | 288 |
| 14278 / write | `0x6c5370` | `693ed1a1e4a317c9fed2fa8dc1dee237e7c670b2aae9ebb97c35c5031402e6dd` | `0x557980` | 424 |

The independently authored target formula is `target_rva = export_rva + 14 + signed_displacement`, with the final jump opcode at thunk offset nine and its signed 32-bit displacement at offset ten. This is the [documented fast-forward boundary](https://learn.microsoft.com/en-us/windows/arm/arm64ec-abi#fast-forward-sequences). The original thunk instruction bytes are not reproduced here or in the codec.

## Complete body extents and instruction set

Original ARM64 exception-directory RVA is `0x9bd000`, size `226360`, SHA-256 `bb690049d07c232ac7c3aaf94b082884a3f8b4eb4c62a02076e2202985659f92`. Its entries are eight bytes, following the [ARM64 unwind format](https://learn.microsoft.com/en-us/cpp/build/arm64-exception-handling?view=msvc-170).

| Role | pdata RVA / SHA-256 | xdata RVA / header | Complete 16-byte xdata SHA-256 |
| --- | --- | --- | --- |
| Read | `0x9e6570` / `ed9eb4c7d994fb77c8e0d094bc3445d1d655da50dbf803bb49c5ebfcba7de049` | `0x92e118` / `0x10400048` | `2a331000e7063be4a96e7826eaaf3f550bf26b3c3b4066af48468b1df930eb22` |
| Write | `0x9e6568` / `f1e9aebf973d123f70abfc031c911fc6ae1c72830f140a9e18167721b5ab3366` | `0x92e108` / `0x1040006a` | `a8911787214b7a4e31bbde001329db103e7cc770d8350c5eaa6769cb98111568` |

Both headers have version zero, no exception-data extension, one explicit epilogue scope and two unwind code words. Their function lengths are `72*4=288` and `106*4=424`. Both spans include all mode-error tails after the ordinary return. The next starts are RVA `0x557c60` after read and `0x557b30` after write; padding and next-function entry metadata are excluded. No first-fragment truncation is used.

CHPE metadata version two is at RVA `0x6fdd70`; its code map is RVA `0x890230`, count three, 24-byte SHA-256 `970b5db8680e06a0a639103ce2970ac3a3640c0a46ea9aabc8a9907c71faaa5c`. The low-two-bit classification agrees with the [LLVM COFF definitions](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Object/COFF.h): `[0x1000,0x33613c)` is ARM64, `[0x337000,0x68e1c8)` is ARM64EC, and `[0x68f000,0x6c6190)` is AMD64. Both body instruction streams decode as ARM64 within the ARM64EC range; both export thunks lie in the AMD64 range. ISA is not inferred from the mapped header alone. The separate mapped AMD64 exception directory at RVA `0x9f4438`, size 180, describes fifteen other helper entries and does not bound these bodies.

The original LLVM read failed on a no-name export-table parser error. For instruction display only, this worker used an in-memory analysis view hiding the export directory from LLVM, with all instruction bytes unchanged. No modified-header identity supplies any hash or original address in this record. All fingerprints use the original pinned file or immutable runtime captures.

## Count grammar and archive context

The native ReadCount body requires archive mode bit `0x1` at `this+0x20` to be set. It reads u16 little endian. A value other than `0xffff` is the count. With that marker it reads u32; a value other than `0xffffffff` is the count. With both markers it reads u64. Buffer cursor increments are exactly two, four or eight in the corresponding branches, with the read-buffer helper at `0x180557780`. Wrong-mode paths take archive-error tails. There is no file-version comparison.

Native WriteCount requires that mode bit clear. For unsigned count `n`, its canonical encoding is:

| Domain | Ordered wire primitives | Encoded bytes |
| --- | --- | ---: |
| `0 <= n < 0xffff` | u16 `n` | 2 |
| `0xffff <= n < 0xffffffff` | u16 `0xffff`, u32 `n` | 6 |
| `0xffffffff <= n <= 0xffffffffffffffff` | u16 `0xffff`, u32 `0xffffffff`, u64 `n` | 14 |

The write-buffer helper is `0x180557640`. The new `MfcCount` rejects a noninteger or a count outside the unsigned 64-bit domain before emitting its count. It reads exactly this grammar and writes exactly the canonical native branch sequence. It never fills in a missing count, row or value. Existing `Rep` rejects a decoded row count above 10000000 before allocating or looping. That decoder safety limit is unchanged; it is not a native u64 domain limit. Existing store repetition still requires list length to equal `n`; it does not have a separate ten-million-item check.

The native reader also accepts an overlong count form, such as the u16 marker followed by a small u32. Native store and `MfcCount.store` choose the shortest native branch for the decoded integer. No width shadow or extra field is introduced, so arbitrary noncanonical-count byte identity is not claimed. Remote byte identity on actual files remains a separate required check.

`require_ordinary_mfc_map` requires the existing ordinary `Core.Load` or `Core.Store` type, including legitimate subclasses, and effective `Dsl.ver(ar)==19000` before this owner processes fields. The shared convention maps an unspecified or zero version to current version 19000. Other explicit versions or other archive implementations fail closed. Core has no native `CArchive+0x20` mode-word field or DB archive implementation. This guard bounds use to the existing ordinary grammar; it does not pretend to inspect an unavailable native flag. In particular, `ctx["conditions"]` is separate vendor helper metadata, not that native mode word. The native DB/no-payload branch is unsupported by this owner.

Vendor `su_CArchive` count has a different grammar. Its verified read span is `[0x31a36ad0,0x31a36b09)`, SHA-256 `6966be20e71e8777d862016dc2f7de54d76ba69a2ba29fe915e7df1d72fe6342`; write is `[0x31a37d70,0x31a37db4)`, SHA-256 `739193155817582f2873825e1fd01be61840e10d11d8c4360e5aea4af85f6517`. Those functions end at u32. There `0xffffffff` is an ordinary u32 value, not a further escape. [Core.py](../../tooling/sw2026/serial/Core.py), `Schema.Cnt`, `Dsl.count` and every existing vendor-count owner remain unchanged. See the [count-family gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/FrameworkAndVendorArchiveCountsDiffer.md).

## Runtime byte evidence and remaining acceptance

The architecture guard in `MfcRuntimeView01` stopped before MFC loading. Its WOW64 classification did not establish actual process architecture; see the [specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Inspection/WowClassificationDoesNotIdentifyProcessMachine.md). `MfcRuntimeView02` then measured AMD64 through ProcessMachineTypeInfo, matched raw and mapped own-executable headers, resolved the effective exports and captured both complete entry windows. Inventory SHA-256 is `2f85846bb67f141d309031b4a8935a212f7f06528e6dddf52e9cedcc9816a398`, under source `067f473f58b6ea804483ff54789c2e78c8e6a0b1`. Those windows matched the pinned raw runtime but did not contain either target body.

`MfcRuntimeView03` used committed source `925536db6adade2a04c1faf44b5516efd1a79110`, tool SHA-256 `f83885f25f9661fff7fc893cd2e5d63fc9db07c5769e983eb25a6c378c93fb71`, fresh owned PID 1760 and the opt-in [count-body capture](../../../Documentation/Changes/Solidworks/Model/SolidworksMfcCountBodyCapture.md). Its immutable inventory SHA-256 is `6907f9bcf6255b0025193f04a4eb773d8914b1917fe5f169fc0539710fe8df1d`; host receipt SHA-256 is `4db5e9f7df0bcbc68d165033d09fb5f5b4d8e48baa72493d2d1f670c063ac03b`. Transport exit is zero. Both complete 288/424-byte captures have the original body hashes above and are literally equal to those original spans. The parent and this worker independently rehashed and compared them. Metadata records exact thunk and target checks, `count_body_bytes_verified=true`, and successful release of the probe's own module reference. Raw03 files remain immutable and external.

The probe's `instruction_set_proven`, `native_implementation_bound` and `acceptance` remain false, as designed for that byte-capture tool; `archive_methods_invoked` is false. The independent static count/body interpretation in this record does not rewrite those flags. No method invocation, native boundary-value experiment or CAD model acceptance is inferred from byte equality. The direct comparison closes the selected loader-byte preservation edge without assuming that every runtime patch source is absent.

Overall confidence is **partial** under the [evidence vocabulary](../../Playbook/Evidence.md). Native dispatch, full extents, mapped-byte identity and branch grammar are grounded. The new owner has had AST/source review only. Remote process-boundary replay, actual-used-schema admission and count-boundary exercises on the new implementation remain pending. Nonempty map semantics, duplicate-key behavior, key encoding limits, malformed inputs, historical versions, DB archives and fresh neutral construction have no new acceptance claim. No donor rows, saved defaults, opaque tails, runtime file reads, native dependencies or writer changes are introduced. Radial callback and complete flag-word closure remain independently unresolved.

## Instructions and stopping conditions

The repository [standard PR skill](../../../.agents/skills/standard-pr-practice/SKILL.md), host reverse-engineering skill, complete [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), full [instruction book](../../Playbook/README.md), [loader chapter](../../Playbook/LoaderAnalysis.md) and [correlation chapter](../../Playbook/CorpusCorrelation.md) govern this investigation. This worker performed static source/AST/metadata/native-byte inspection only, with no schema, codec, product or test execution, held-out CAD payload reads, VM access, CAD/COM, service or licensing actions. Only independently authored format knowledge is reproduced.

> YOU DO NOT HAVE THE ORACLE. DO NOT LAUNCH, ATTACH TO, OR AUTOMATE THE CAD APPLICATION. REQUEST MEASUREMENTS FROM THE ORACLE OWNER.

> The first is success under every criterion on this page.
> The second is the end of the available context.
> Missing grammar is the work. It is not a blocker.

This is a bounded source-schema handoff. The overall CAD goal and fresh generated output acceptance remain unfinished.
