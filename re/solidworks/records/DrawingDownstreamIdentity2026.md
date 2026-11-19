# SOLIDWORKS 2026 downstream edge identity

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID`, owner `configuration_header`, delivery PR #121. This source-only tranche follows the [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), [RE playbook](../../Playbook/README.md), [existing edge-map callback](DrawingDetailingEdgeMap2026.md) and [four surface-role proof](DrawingEdgeSurfaceRoles2026.md). Its exit is a pinned allocation/storage/rebuild trace and an explicit construction boundary. Full native construction and public drawing admission remain unfinished.

The native allocation uses a model-wide counter. A downstream edge ID is neither a sketch marker, a feature persistent ID, a kernel node ID, nor a zero-based portable edge suffix. The surface-role references identify geometry; the downstream key identifies a separately allocated cache association.

## Exact build and custody

[Source ledger](DrawingDownstreamIdentity2026.json) pins the original `34.5.2.0604` module hashes, complete PE-unwind ranges, small exact leaf/thunk ranges, import/export identities and schema tokens. Licensed modules and all instruction listings stay outside the checkout. The REA/Hopper `getEdges` dossier is `ev_27eef1c01fbd650c6a5fbb7714cc161d5631de9cf3eb34dade52e5417ec7b646`, bound to backend SHA-256 `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`. Hopper could not provide full function bounds; original PE unwind data independently pins that body. The owned target was closed and its immediate status was `open=false, cleanup_pending=false`. No foreign target was touched.

The two previously disclosed drawing sources and their shared child are only inherited research authorities. Their earlier [31-process role/rail proof](../measurements/2026/DrawingEdgeRailCorrelation01.json) and [16-process omission diagnostic](../measurements/2026/DrawingFrontDetailingMapOmission01.json) are not new observations or new held-out credit. This tranche opens no CAD payload and runs no vendor process.

## Attribute and owner domains

`gcEnvironment_c::getDownstreamIdFromEdgeAttr` (`sldgcu!0x439d5240`) reaches `0x43e744f0`, which calls the same edge getter dispatch reached by `gcEdge_w::getDownstreamId`. The dispatch's import at `0x43f5a848` names the exact backend getter at `sldgciParau!0x32f93600`. It returns only the first word to the drawing callback. The ordinary callback skips zero and stores the nonzero unsigned key with its actual `moEdgeRef_c`; the existing consumer later looks up that key. The callback's separate kernel node ID remains a different domain.

Backend registration at `0x32fa091d–0x32fa094f` binds the literal `DOWNSTREAM_EDGE_ID` to `gciTopEnt_w::edgeType`. The setter at `0x32f953b0` writes field zero as exactly six signed 32-bit words carrying these bit patterns:

| Word | Owner |
| --- | --- |
| 0 | Allocated unsigned downstream ID |
| 1, 2 | Low then high words of the edge update `FILETIME` |
| 3 | Integer context; the demonstrated fresh ordinary path supplies the model's `isAssembly()` result |
| 4, 5 | Low then high words of the downstream model-owner key |

The getter reconstructs all of those outputs. Its old-array branch supplies context zero when the integer count is at most three; that fallback does not qualify malformed short arrays for SDK use. When the setter discovers an existing attribute itself, its no-rewrite comparison checks ID and `FILETIME` only. A caller-supplied existing attribute takes the explicit rewrite path. Context or owner changes alone therefore cannot be assumed to refresh every existing attribute automatically.

`moModel_c::getDownstreamIdData` at `0x4b285fc0` reads runtime model member `+0x1348`. This is `moDownstreamIdData_c`, not `moEntRefDownstreamIdData_c` embedded under an edge reference, and not the unrelated UI Definition integer with the same offset spelling.

The data object's `+0x30` string is initialized empty. Registration fills an empty string using `GetSWGUID` (`sldutu!0x3d036390`: `UuidCreate` then `UuidToStringA`) and computes `+0x38` using `ut_64BitHashCString`. The latter is not a raw pointer or an FNV hash. Its exact source rule is:

`p(b) = sum(utf16_unit[i] * b**i) mod 1000000009`

`owner_key = (p(32771) << 32) | p(32779)`

The complete `0x3cfa0440` and `0x3cf9fe60` ranges establish the two bases, modulus, initial power one and UTF-16-unit order. Registration maps that key to an actual `moModelHandle_c` in global `0x4db56820`. `s_getEdgeDownstreamIdAndModelOwner` at `0x4b538440` dispatches the appropriate typed getter and resolves the returned key through this map. No new runtime GUID/hash equality or collision guarantee is claimed here.

## Allocation, persistence and rebuild

| Stage | Pinned source rule |
| --- | --- |
| Fresh data | Constructor `0x4b51d470` sets the next-ID word at `+0x08` to one |
| First creation | `0x4b526500` calls face creation before `0x4b526568` calls edge creation |
| New edge | `0x4b52ae4a–0x4b52ae52` consumes and increments the same shared next-ID word; the row stored under `+0x60` contains an actual `moCompEdge_c*` and its allocated ID |
| Backend edge order | Part branch `0x4b52d29c` calls `gcBody_w::getEdges`; backend `0x32fd8ed0` calls delay import `PSKERNEL.dll!PK_BODY_ask_edges` via `0x330a0d63` / IAT `0x3312aeb8` and preserves returned order while widening tags |
| Attribute attachment | `0x4b52f420` obtains the actual edge from the parallel edge table and uses the allocated ID, retained or current time, actual context and model-owner key in the setter call at `0x4b52f626` |
| Archive | Serializer `0x4b51fee0` writes the next-ID word first, then typed containers. The edge table store at `0x4b520058–0x4b5200a8` emits each actual `moCompEdge_c` through its archive pointer operator and writes its ID |
| Owner archive | Version `>=0x3359` writes the UUID string, then owner-key high32 and low32 at `0x4b5206d5/0x4b5206e9/0x4b5206f4`. This differs from the low/high order inside the kernel attribute |
| Ordinary load | `0x4b5860e0` opens `Contents` and the active configuration's actual storage name plus `-DownstreamIdData`; `moBaseConfiguration_c::getStorageName` is `0x4bdda870`. It invokes the concrete serializer, registers the model owner at `0x4b586317`, and attaches the object at `0x4b58631c` |
| Rebuild | `0x4b5313e0` tries actual stored edge semantics and retained attributes. `0x4b52b980` asks the reuse helper before consuming a fresh shared ID. It can reuse an empty vector slot independently of the numeric ID. `getCompEdgeFromUniqueID` at `0x4b5287f0` maps a key to a stored edge-table index and returns the actual component edge |

The owner-load branch additionally clears UUID/key when `moArchiveHelper_c::isAddingNewConfig()` is true. That context is distinct from an ordinary same-configuration load. The complete downstream model codec, all optional modes and its condition-`0x80` embedded branch remain unqualified; the SDK's existing explicit refusal is preserved.

## Verification and next construction boundary

The [metadata verifier](../../tooling/sw2026/drawing_edges/VerifyDownstreamEvidence.py) checks immutable module identities, 35 native source ranges, three schema literals, eleven exports, eight direct imports and the delayed kernel import. It reads original modules without executing them and emits hashes and conclusions only. [Source receipt](../measurements/2026/DrawingDownstreamIdentitySource01.json) binds this inspection; it is not a CAD round trip or native acceptance test.

```sh
python -I -B re/tooling/sw2026/drawing_edges/VerifyDownstreamEvidence.py \
  --root /absolute/Kit --bin /licensed/pinned/bin \
  --record /absolute/Kit/re/solidworks/records/DrawingDownstreamIdentity2026.json \
  --record-sha256 b748b5d4146891d30b743e77d7044aee7de9405300f1a4101600fe2f9d783bf1 \
  --output /unused/private/DownstreamSource.json
```

A writer must first derive the exact body/face/edge traversal from its generated topology and carry one shared allocation history. Matching four surface roles to an analytic rail does not supply its downstream number. Reusing captured keys, inventing portable-edge ordinals, or publishing only the six words without their owner graph would not meet the no-donor or full-ownership criteria. No writer code, cache, captured rows or defaults are introduced.

The smallest next native discriminator is a passive, root-owned same-input trace around the initial edge allocation and setter while COM alone opens, rebuilds and saves a disposable disclosed drawing/child pair. Bind the exact session-owned process, module hashes and restored breakpoint lifecycle. Observe only whether `data+0x08`, setter ID and the drawing insertion key agree for the same actual edge; retain pointer values privately and publish only equality and metadata. A healthy native control must prove the trace before any generated candidate. The result would qualify an observed path, not by itself derive `PK_BODY_ask_edges` order from a neutral graph. No native packet is executed or claimed by this tranche.

[Shared-counter gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DownstreamKeysAreSharedModelIds.md) · [Change](../../../Documentation/Changes/Solidworks/Inspection/Drawings/Downstream/SolidworksDrawingDownstreamIdentity.md)

The generated partition projection now follows the single-solid topology links and assigns the actual face and edge attributes. Its guarded host replay is recorded separately. [Generated attributes](GeneratedDownstreamPartition2026.md)
