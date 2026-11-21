# Fresh downstream reference assignments in SOLIDWORKS 2026

**Exact source binds the scoped construction provenance.** This checkpoint binds ordinary part face/edge row assignment, the embedded signed adjacent-face map and the initial coedge choice. It identifies the first remaining model-derived dependencies rather than replacing them with constructor-only defaults.

Task `PR121-DownstreamFreshReferenceAssignments`, owner `configuration_header`, delivery PR #121. Root owns SDK integration, generated adjacency proof, native oracle and publication. Dependencies: [archive grammar](DownstreamIdArchiveGrammar2026.md), [component bodies](DownstreamComponentWire2026.md), [direct entity-reference bodies](DownstreamEntityReferenceWire2026.md) and [kernel traversal](ParasolidBodyTraversal2026.md). No CAD file, hidden input, vendor process or SDK product execution was opened by this tranche.

## Exact source authority

The [numeric ledger](DownstreamFreshReferenceAssignments2026.json) binds 70 complete function entries and 101 function fragments, plus five complete delayed-import jumps and four topology-type vocabulary intervals. [Metadata verification](../measurements/2026/DownstreamFreshReferenceSource01.json) rechecked all 110 intervals against four original modules. Function bounds include chained PE unwind fragments. Small leaves stop at the actual return/tail jump. No instruction listing, binary, captured CAD row or native payload is enclosed.

| Original | SHA-256 | Preferred base |
| --- | --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | `0x4b140000` |
| `sldgcu.dll` | `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594` | `0x43740000` |
| `sldgciParau.dll` | `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce` | `0x32f70000` |
| `PSKERNEL.dll` 37.01.250 | `2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969` | `0x180000000` |

The [verifier](../../tooling/sw2026/downstream/VerifyFreshReferenceAssignments.py) reads these files as bytes, never as executable code. It takes `--bin-directory`, explicit `--kernel`, `--record` and an unused `--output`. Its passing receipt is source custody only, not a product test.

## Fresh owner graph and ordering

`moModel_c::createDownstreamIdData` constructs the actual data object and enters a construction scope before invoking `0x4b5263c0`. At `0x4b578818`, leaf `0x4b51de40` publishes that actual object to global `0x4db5dd20`. The function at `0x4b51f880` clears it afterward. This is not the archive helper's `SerializingDownstreamIdData` flag.

While this scope is active, BEnt semantic initializer `0x4b74bfc0` constructs `moEntRefDownstreamIdData_c(actual BEnt)` at `f18` if absent. Getter `0x4b74f190` returns its signed map at `&f18.f10`. A bare default reference outside this scope does not supply those semantic associations. A portable implementation must express this as explicit graph ownership and model context, never a CAD runtime or native global requirement. [Active-scope gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/EntityReferencesNeedDownstreamConstructionScope.md)

The fresh orchestrator stores its actual model at data `f6d0`, obtains the body inventory, calls face construction at `0x4b526500`, then edge construction at `0x4b526568`. The native default counter `f08` begins at one. Each allocation consumes the current value and increments it. This proves shared allocation ownership, not a universal saved prefix or a geometry-only ID formula.

Ordinary part body collection (`0x4b538110`) uses the actual `moAtomManager_c` at model `fd88` and its `getBodies` method. The output array is downstream `f690` (`f698` pointers, `f6a0` count). Native order is retained. Rollback, model-state and nonempty-output guards precede it. Arbitrary multibody inventory/order is not newly derived here.

## Actual face and edge rows

| Step | Face `f48` | Edge `f60` |
| --- | --- | --- |
| Geometry order | Body `getFaces` retained order through `0x4b52d550` | Body `getEdges` retained order through `0x4b52d210` |
| First semantic object | `moFaceRef_c::get(face,model,0)` at `0x4b52b294` | `moCompEdge_c(edge,component,1)` at `0x4b52ad43` |
| Retry | Predicate `0x4b538ca0` can discard and rebuild FaceRef with mode 1 | Validation `0x4b525960` can discard and rebuild CompEdge with mode 0 |
| Component | Actual body-to-component map `f6b0` with `getSelfComponent` (`model.f990`) as the fallback | Same ownership selection |
| Wrapper | `moCompFace_c(actual FaceRef,actual component)` | Actual CompEdge, whose constructor obtains the component's real filed owner and builds the EdgeRef |
| Body identity | Actual `gcBody_w::getAtomId`, explicitly copied to wrapper `f18/f1c` | Same explicit copy |
| Allocation | Read/increment data `f08` at `0x4b52b38e/396` | Read/increment at `0x4b52ae4a/52` |
| Stored row | Actual wrapper pointer and allocated u32 ID bits | Actual wrapper pointer and allocated u32 ID bits |
| Parallel entity | Actual face appended to runtime `f6d8` vector | Actual edge appended to runtime `f6e8` vector |
| Lookup | `f480`: actual face → checked zero-based `f48` row index | `f4c0`: actual edge → checked zero-based `f60` row index |

A vector row is 16 runtime bytes. Its archive pointer has variable object framing. The row's downstream number, vector index, body atom and native entity node ID are distinct domains.

Face registration calls `0x4b5293d0` with type `0x138c`, allocated ID, row index, actual body atom and actual face node ID. Edge uses type `0x138a`. Both have later validation/replacement branches: the pointer in the existing row can change while the allocated ID stays unchanged. Counter position alone does not select a valid semantic reference object.

The FaceRef mode predicate returns true for at most three ID records, or fewer than four distinct nonnull representation pointers for a larger array. It counts the actual pointer identities.

Existing component constructor rules still apply: actual component `virtual+0x158(0)` supplies owned component state. Do not replace that operation with an assumed alias. Source surface-ID reps also carry actual feature/FR/external and epoch owners required by construction.

## Exact signed key/value join under `BEnt.f18.f10`

Indexed insertion is `0x4b74bf60 → 0x4b53b540`. The first helper requires active construction scope and a nonnull actual face. The second rejects negative signed role keys, then calls `0x4b528a90` with that face. That lookup:

1. Finds the actual face in data `f480`
2. Reads its signed row index and checks it against the actual `f48` vector size
3. Returns the allocated u32 ID from that row's `+8` word

Only a nonzero result is inserted. The signed-key tree subscript at `0x4b2d29b0` returns the existing value slot for an equal key or inserts a new node. `0x4b53b57d` assigns that slot. Thus the second word is the actual face row's downstream ID, not a face node ID or vector index. Its wire type is i32 carrying the unchanged low32 bits of the allocated u32 ID. The test is nonzero, not signed positivity.

The native serializer at `0x4b53b0b0` walks this tree in ascending **signed key order**, writing key then value. It does not sort by the face ID or geometry. Failed/zero-ID calls neither insert nor erase an existing association. Repeated successful assignments to the same key overwrite. Equal face IDs at different keys retain separate entries.

On the coedge-backed ordinary role path:

| Signed key | Actual role | Insertion condition |
| ---: | --- | --- |
| 0 | Selected coedge's left face | Called for every edge. Skips null or unregistered faces. |
| 1 | Selected coedge's right face | Same rule, including a face shared with the left role |
| 2 | Selected coedge's start face | Previous-coedge edge-ID lookup failed and fallback face exists |
| 3 | Selected coedge's end face | Next-coedge edge-ID lookup failed and fallback face exists |

The wrappers bind left to `selected.face`, right to `selected.partner.face`, start to `rightFace(selected.previous)`, and end to `rightFace(selected.next)`. `rightFace` (`sldgcu!0x439133e0`) checks null self/partner and does not compare the returned face with the left face.

Therefore, when a two-fin seam has the same real face on both incidences and reaches this role path, keys 0 and 1 retain the same face ID as two entries. This is a proved insertion/getter rule, not full native qualification of arbitrary seam references. Later ambiguity, factory fallback and validation remain separate. [Duplicate-role gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/AdjacentFaceRoleMapsKeepDuplicateIds.md)

## Initial coedge: positive fin, not unconditional primary

The EdgeRef entity constructor (`0x4b748400`) calls the **no-argument** `gcEdge_w::coEdge()` overload and forwards its result before the model-dependent construction branches. It does not request reversal. The chain is:

`model 0x4b748436/444 → sldgcu 0x439a9390 → 0x43e78710 → sldgciParau 0x32f92510`

Backend `coEdge` first calls `getFirstCoEdge` through `PK_EDGE_ask_first_fin`. In the plain kernel path, that API starts from actual `EDGE.halfedge` at runtime `+0x50`, preferring a live loop-owned incidence. If the primary has no loop, it can select the next incidence instead. Closed two-fin solids have both actual loops and remain in the simpler branch.

`getType` is **edge topology**, not curve class. It returns the third `PK_EDGE_ask_type` result minus `0xe74`. Exact vocabulary binds 0 wire, 1 laminar, 2 normal and 3 nonmanifold. The plain kernel type calculation returns normal for exactly two live incidences containing both positive and negative senses.

At `0x32f92567`, the backend obtains the actual edge curve and only tests nonnullness. There is no kind-30 line versus kind-31 circle test. With a nonnull curve and topology type other than laminar, it tests `PK_FIN_is_positive` and substitutes `partner` when false at `0x32f92585`.

The exact kernel positive test at `0x18031836d` compares `HALFEDGE.sense` at runtime `+0x60` with `0x2b` (`+`). The partner wrapper calls `PK_FIN_ask_next_of_edge`. For two live fins this follows `HALFEDGE.other` at `+0x30`. It returns null if the API returns the same incidence. Neither operation compares downstream IDs or portable edge indices.

The independent HALFEDGE field registration (`[0x18143fc20,0x181440016)`) binds `loop +0x10`, `forward +0x18`, `backward +0x20`, `other +0x30` and `sense +0x60`. EDGE registration independently binds `halfedge +0x50`. This supplies the field-to-instruction join, not an index correlation.

**Bounded neutral rule:** for a classic normal edge with exactly two live loop-owned opposite-sense fins and a nonnull actual curve, choose the unique fin whose `sense` is `+`, whether it is the transmitted primary or its `other`. This applies to ordinary lines and circles. Then derive role keys from that selected incidence.

Laminar edges skip the sense test. Missing curves invoke additional mixed/classic-category conditions. Wire/ACIS, nonmanifold, special representation and unmatched factory branches remain outside this rule. No live API orientation observation is claimed. [Primary-fin gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/EdgePrimaryFinCanChangeBeforeReferenceCreation.md)

## Directly adjacent solid-body row

The nearby `f90` creation is conditional: ordinary part, runtime option `0x4db5681c & 0x10`, the retained body inventory and actual solid classification. It is not a universal requirement that every fresh part has a body row.

The CompSolidBody constructor receives actual component/body atom ownership. Appender `0x4b524ba0` requires parallel body vector `f708`, a nonnull actual `moFaceRef_c` at component `ff0` with actual ID data, and role-0 resolution to a real face. It then consumes the same `f08` counter and appends component pointer/ID to `f90`, with the actual body retained separately. A fresh empty wrapper whose representative reference is null does not satisfy this path. The constructor calls the FaceRef factory at `0x4b7e8d1d` and stores that owner at `0x4b7e8d22`. Full representative-face selection and optional body-row generation remain open.

## What is ready and what remains

Field assignment, role-key/value ownership, duplicate-map behavior, ordered store and the bounded positive-fin choice are confirmed static source rules. They can guide an explicit model-derived implementation. The exact source receipt does not qualify generated output or a full recursive downstream stream.

The first unresolved inputs are actual surface/edge representation owners, factory multi-match/fallback and live cache state, previous/next edge-ID availability for keys 2/3, the remaining embedded vector/scalar semantics, body representative references and general body inventory/order. Root's separate generated topology/adjacency proof and controlled native comparison must address those before writer admission. Previous frozen default outputs and source packets are unchanged.
