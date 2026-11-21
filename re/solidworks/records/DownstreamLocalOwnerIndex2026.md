# Actual local-owner index setup and the empty encoded table

**The generated prism encodes an empty CMgr external table, but that alone does not prove that runtime index zero is still available when partition repair runs.** Native source proves first-local insertion into a fresh empty list, indexed lookup and the missing-index fallback. Absence of every possible intervening foreign insertion remains a separate lifetime condition.

Task `B04-SW2026-DOWNSTREAM-RUNTIME-OWNER`, owner `flag_ownership`, delivery PR #121. Root owns publication, the generated part, native verification and the VM. This additive packet preserves the earlier [pointer domains](DownstreamRuntimeOwnerPointers2026.md) and [ordinary load repair](DownstreamPartOwnerReload2026.md) packets unchanged.

## Exact sources and bounds

Original source verification covers 23 complete functions, 15 unwind fragments, 14 instruction windows, two RTTI windows, eight virtual cells, twelve imports and ten current source files. The recorded windows scope the allocation and load behavior. [Numeric ledger](DownstreamLocalOwnerIndex2026.json)

| Original module | SHA-256 |
| --- | --- |
| `sldmodu.dll`, build `34.5.2.604` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldarchiveu.dll`, build `34.5.2.604` | `5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48` |

RTTI binds the manager constructor table `0x4cf5af28`, complete-object locator `0x4d330480` and type descriptor `0x4db35228` to actual `moFeatureRefMgr_c`. Import and virtual targets are read from unchanged original PE images. Stateless LLVM was used. No vendor code/listing is distributed and no vendor function was called.

## What the named generated source actually encodes

The census reads the named generated source declarations and their field assignments.

| Exact source owner | Authored structural rule |
| --- | --- |
| `CheckPrismFaceConstructors.authored_prism` -> `builders.Part.construct_part` -> `builders.Model.configuration_manager` | Sets `n_ext=0` and `ext=[]`, along with the other empty context/reference collections. |
| `builders.Metadata.header` and `Part._metadata` | Header external directory `f30=None`; a separate self-file object is assigned to header `f38`. |
| `builders.ExternalFiles.ordinary_self_reference` | That self-file object has its own initial `f78=-1`, actual generated file identity and active configuration pair. It is not an indexed FR-manager row by definition. |
| `para.rectangle.ArchiveAttachment.archive_for_oracle` | Changes completed stamps, atom/body attachment and manager configuration stamp. It adds no manager external-list entries. |
| `CheckPrismMgr` used by `read_prism_face_owners` | Requires every manager collection, including `ext`, to remain empty. |
| `para.concentric.CylinderFace.make_feature_file` used by `prism_face_constructor_fields` | Creates a distinct local cache FR wire owner with `f78=0`, a shared copy of the actual generated self-file definition and the actual current configuration. Constructing that node is not native table registration. |

The header map, archive object index, configuration ID, external-reference index and cache owner have separate producers. The typed witness declares its wire index explicitly. Native insertion follows the live rule below.

## Fresh runtime manager ownership

The inspected model-construction window calls `[0x4bb366a0,0x4bb3673e)` with the actual model and installs the result at model `+0xaa0`. That constructor retains the model at helper `+0x08` and initializes its external list at `+0x20` to null.

The CMgr default constructor at `0x4b880dd0` calls `0x4bb36600` and installs its distinct helper at CMgr `+0x4b0`. The overload retains CMgr at helper `+0x10` and initializes helper `+0x08` and external list `+0x20` null.

The ordinary CMgr loader at `0x4c21ef40` reads the external count at `0x4c22003f`. Positive counts enter the incoming-object share loop at `0x4c220053..0x4c2200d2`. Count zero adds no incoming object through this branch.

List initialization at `0x4bb37180` and `shareXModel` at `0x4bb37400` use the actual CMgr manager list when available. The alternative constructs a fresh `moExtObjectList_c` for that owner.

## First local insertion and index lookup

The resolver constructs a local file object from the actual part and configuration, then shares it before looking up the mirror. The named external constructor `[0x319fb380,0x319fb4cb)` initializes its `f78=-1`. The fresh external-list constructor `[0x319fb090,0x319fb0da)` initializes maximum index `+0x4c=-1`.

When the list is actually empty and remains so until this insertion, the share path appends the actual local object at `0x4bb3762c`, then calls `setExtObjToIndex` at `0x4bb37639`. Its complete leaf `[0x31a01690,0x31a016b0)` increments the fresh maximum from `-1` to `0` and assigns that value to the new object's actual `f78`. This proves index zero for that construction sequence without borrowing a saved row.

`getExtObjFromIndex`, `[0x31a00190,0x31a00200)`, first asks the actual keyed map, then scans list objects for matching `object+0x78`. It does not select the first list position. Missing index returns null. Its SHA-256 is `789afedad29d421d7b42fb80276f2f4868ed727e44302fdcbec770eb1908ff8f`.

## Resolver outcomes and comparison domains

| Actual runtime state when mirror zero is resolved | Bound result |
| --- | --- |
| Fresh empty list, no intervening insertion, then successful local share | Local receives actual index zero and indexed lookup returns it. |
| Index zero exists and passes native external-object `operator==` against the local object | The resolver can select the current local canonical object and normalize the mirror to its real index. |
| Index zero exists and fails that native comparison | The resolver returns the indexed object. It can therefore return a foreign owner; locality is not forced. |
| Index zero is absent after local construction/sharing | The resolver falls back to the local object. Mirror writeback additionally requires an actual active configuration, `isViewerModel(0)==false` and a nonnegative local index. |

External-object slot `+0xe0` reaches `[0x319fc210,0x319fc345)`, SHA-256 `a2175eadc57796219397e6754972380638d752cdb95336f3828b71145d9a8094`. The ordinary comparison uses native type, shared-definition kind, creation identity and `getRuntimeName` through the native string comparison. Configuration matching belongs to the separate `shareXModel` operation. The exact string comparison normalization remains open.

`shareXModel` has a separate selected configuration-matching argument: the actual resolver passes it as one, so sharing compares configuration ID and name separately. Do not merge that sharing predicate into `operator==`. In particular, an indexed same-file object can be canonicalized to the actual local/current-configuration owner by the resolver's equality branch even when its configuration differs.

## Remaining condition and replay

The source binds the encoded empty table, fresh constructors and first-local insertion. The interval from manager initialization to repair at `0x4c1b797a` still needs a complete call-order proof for foreign insertion. If a different file occupies index zero, it remains an eligible indexed result.

Run the preceding [VerifyRuntimeOwnerSources.py](../../tooling/sw2026/downstream/VerifyRuntimeOwnerSources.py) against this ledger and the two unchanged original modules to check the native pins, groups, windows, imports and cells. The source declarations have independent whole-file hashes and exact line ranges in the ledger. No source file was changed, and no generated or saved CAD file was opened by this analysis.

See the [encoded-table versus runtime-list gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/EmptyWireListDoesNotProveRuntimeIndex.md). No VM, held-out input, product, schema, codec or test was used. Cache-bearing native load/rebuild/edit/save/reopen and C10 remain unqualified by this packet. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and full [RE playbook](../../Playbook/README.md) apply. Their stopping conditions remain: “The first is success under every criterion on this page.” and “The second is the end of the available context.” Root owns native measurements and completion claims.
