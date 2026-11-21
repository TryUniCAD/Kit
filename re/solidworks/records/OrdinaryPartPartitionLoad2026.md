# Ordinary part partition load, SOLIDWORKS 2026

This checkpoint distinguishes the ordinary part load from the previously bound future-version loader. It pins the path from storage model loading through the part/context/storage calls to partition receive and active-body publication. It does not identify which of those stages failed in the disclosed generated prism opens.

Task `B04-SW2026-DOWNSTREAM-ID-DATA`, ordinary prism admission subtask; owner `flag_ownership`; delivery PR #121. Root owns native measurement and integration. The [numeric ledger](OrdinaryPartPartitionLoad2026.json) contains six exact original image identities, 20 complete functions, 15 instruction windows, 12 virtual cells and 25 imports. The [static receipt](../measurements/2026/OrdinaryPartPartitionLoadSource01.json) records the source replay. No vendor code or listing is included.

## Ordinary entry and configuration selection

In pinned `doccplu.dll`, exported `SolidStorage_c::LoadModel` is `[0x1800226d0,0x180022ddf)`, SHA-256 `1b79c436e7755212fb3ffff395c878a8a44564ee0e82a07bc77ffe2d5d1f0dfd`. After earlier model/storage work, it obtains the actual configuration's opened model. The selected call at `0x1800228b4` imports `moPart_c::loadExternalBodies`. Its immediate gates require the actual model's part-kind result to equal 1, a false document future-version flag and a false reached application virtual `+0x3d8`. This checkpoint does not rename that last application predicate or claim that a static gate was observed running.

`moPart_c::loadExternalBodies` is `[0x4c23e4f0,0x4c23f778)`, SHA-256 `c1182102c7c3336019c2945f76cf1d350ae1c3df0a4649e89583ceecdf4ace8f`. It selects the supplied actual configuration, otherwise the active configuration at part `+0xd78`. It obtains that configuration's real storage name, derives its `-Partition` name, and keeps distinct `-StockBodies`, `-Body` and `-ACIS` branches. Kernel-selection and existing-partition branches precede the selected context call. A mere matching archive stream name does not prove which branch ran.

The ordinary selected context call is at `0x4c23e7d9`, through model context virtual `+0x540`. The actual `ModelDocModelContext_c` table `0x4a65d908` binds this cell to import thunk `0x4a31a41d`, IAT `0x4a469c80`, for `BaseDocModelContext_c::loadPartition`. That complete method is `[0x458eefc0,0x458ef068)`, SHA-256 `dd59bfbe83a58ef5677e79713bc676c5e3080c6f63e6f8675f78602ff4c40216`. It obtains the document's actual solid storage and calls its virtual `+0x500`, preserving the actual name, version, model, ghost selector and additional string.

The original `SolidStorage_c` and `SolidStorageMFC_c` tables both bind `+0x500` to exported `SolidStorage_c::LoadPartition`, `[0x18002c270,0x18002c570)`, SHA-256 `14fc62b147d0ae4f4abcc12798cf4f54840a88a83fd2a3f33bea0b04fb2363ef`. The source-bound constructor tables are also described in the [standalone store record](DownstreamStandaloneStore2026.md). Installation of that concrete storage manager in the selected live document remains separate: `uiBaseDoc_c::getSolidStorage` reads document `+0x4a8` and calls manager `+8`. Table equality does not prove a live receiver.

## Receive and publication are separate stages

| Stage | Bound native rule |
| --- | --- |
| Actual archive open | `gcPartition_w::loadFromStorage`, `[0x439988f0,0x43998b10)`, branches around restore when either named-storage or selected-stream attachment fails |
| Restore output | The output partition starts null; the wrapper calls `gcPartition_w::restore` at `0x43998aaf` and returns its output pointer |
| Backend receive | `gciPartition_w::restore`, `[0x3305ad80,0x3305b074)`, initializes the kernel output tag to zero, calls the previously bound `PK_PARTITION_receive` path, and stores the signed returned tag as its partition handle |
| Optional deltas | The separate `restoreDeltas` call at `0x3305aee6` requires a nonzero received tag and nonzero passed delta flag. The storage caller's flag calculation retains string/platform/preference and ghost conditions; no universal delta flag is declared here |
| Active body enumeration | `loadExternalBodies` installs each nonnull selected partition at `0x4c23edcc`, then calls its actual `getBodies` at `0x4c23ede5` |
| Model and owner state | Each returned body is cleaned and attached to the actual part; the caller obtains timestamp and atom ID and explicitly performs the already bound owner repair |
| Part publication | A positive body atom ID or exactly one returned body can reach `replaceBody` at `0x4c23f17d`. Its feature/type/error/output-atom gates remain applicable. Current-version lack of an output atom is not repaired by inventing an atom in this branch |

Thus geometric deserialization, active partition state, and publication through the actual feature/atom graph are distinct proof obligations. The [previous receive record](PartitionReceive2026.md) identifies the actual kernel delay-import endpoints. The [owner-repair record](DownstreamPartOwnerReload2026.md) remains valid for its positively bound selected calls. Neither record established a successful invocation on these failing opens.

## Kernel marks are not persistent node IDs

Actual `moPMarkRecord_c` RTTI binds table `0x4d17e9a8`, serializer slot `+0x28 -> 0x4bb1a840`. Its complete serializer `[0x4bb1a840,0x4bb1a8b9)` has SHA-256 `9c304975ba308185c5d0278a791fbae60914456cd1231096b84428db6a6142ad`.

Store uses `gcPMark_w::getId()` when the runtime pointer at record `+0x10` exists; otherwise it writes the stored signed integer at `+0x18`. Load reads only the signed integer at `+0x18`. `moAtomFeature_c::getPMark` reads feature `+0x3d0` and returns that record's runtime pointer or its sign-extended saved ID. These are kernel mark identities, not feature `f08`, atom ID, archive object-map index, or a fixed feature ordinal.

The reviewed block in complete `moRegenRunTimeData_c::s_resolvePMarkAndBodies`, `[0x4c3378a0,0x4c338d5f)`, builds a map from actual partition `getPMarks` and each mark's `getId`. It looks up the model record reached through actual model `+0xe38`, and feature mark records, by exact ID. A successful model-record hit installs the runtime pointer at `+0x10` and clears its integer at `+0x18`. Missing lookup, selected kernel, invocation and subsequent failure paths remain explicit. This checkpoint does not claim every normal open reaches that block, nor infer a default ID from a native save.

## Future-version path correction

`moModel_c::loadFutureModelBodies` first requires model context and context virtual `+0xa20`. The actual base and model-document tables resolve that predicate to `BaseDocModelContext_c::getIsFutureVersionDocument`, an 11-byte leaf reading owning document `+0x4fc`. The actual model-document `+0xa30` is an override reading its own document pointer at context `+0x10`; the base getter reads context `+8`. Both reach document `+0x508`, but the receiver owners must stay distinct.

The earlier positively bound model `+0x1a58 -> 0x4c1b7600` calls therefore remain a conditional future-version path, not a substitute for the ordinary `loadExternalBodies -> context+0x540 -> storage+0x500` chain. [Specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/FutureBodyLoadingHasItsOwnContextGate.md)

## Disclosed result and remaining discriminator

This lane independently hashed/read JSON metadata only from root's disclosed generated-prism experiment. `Result.json` SHA-256 `9050f43ef2c4bf0e90933797733b7155b9bd6016cffbfb21abdd9ff6c0427153` reports both controls healthy and warning 32 on four generated opens. Its body measurements follow explicit rebuild, so they do not show a successful initial receive. `EditResult01.json` SHA-256 `4c8acad55123d7d8e24fbebcf182f953f56daf086c36c131dfb1f33d6fb3a5ed` explicitly retains `clean_initial_opens=false` and `lifecycle_passed=true`.

Root's later comparison removes allocated downstream IDs and the cache stream, while ordinary local zero-key `DOWNSTREAM_FACE_ID` and its timestamp remain. That newer experiment was parent-reported; its raw receipt was not independently rehashed in this checkpoint. It does not establish complete absence of kernel attributes.

The next discriminator is the first failed stage among selected stream attachment, kernel receive/tag, active body enumeration, actual kernel-mark lookup and feature/atom publication. Body timestamp versus model-header body stamp is a separate follow-up; the immediate ordinary timestamp site stores its result in an atom-ID map and does not itself compare the header. No saved value, mark, timestamp or changed writer default follows from this packet.

Source replay verified all six image hashes, complete declared unwind groups, original span hashes, selected imports and virtual targets. The initial metadata replay failed because its grouped imports and missing explicit `cell` key did not match the existing verifier interface; only metadata shape changed before the passing replay. No product/schema/codec/test, VM or REA/Hopper execution occurred. Earlier packets are immutable.

These findings are **partial source-backed rules**, with no measured execution of the selected gates. No native-loadability or held-out acceptance claim is made. The CAD criteria retain both stopping conditions: “The first is success under every criterion on this page.” “The second is the end of the available context.”
