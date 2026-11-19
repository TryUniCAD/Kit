# Runtime face-owner pointers and mirror repair in SOLIDWORKS 2026

Ordinary downstream face getters pass repair mode zero and read the owner pointers already present. The integer mirror resolver uses the actual file-reference list index, including index zero.

Task `B04-SW2026-DOWNSTREAM-RUNTIME-OWNER`, owner `flag_ownership`, delivery PR #121. This source checkpoint extends the immutable [membership](DownstreamIdentityMembership2026.md), [local-owner](DownstreamLocalOwnerContext2026.md) and [surface-copy](DownstreamCollectedSurfaceClones2026.md) findings. Root owns integration and the oracle. The exit for this checkpoint is exact pointer/mirror ownership and the actual getter's repair mode, with the ordinary preparation caller retained as unresolved.

## Original image and method

Source verification covers 34 complete functions, 38 declared unwind fragments, 13 instruction windows, one table window, six virtual cells and 21 imports. The selected attribute-list helpers are scoped to owner conversion. [Numeric ledger](DownstreamRuntimeOwnerPointers2026.json)

| Original module | SHA-256 | Preferred base |
| --- | --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | `0x4b140000` |
| `sldgcu.dll` | `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594` | `0x43740000` |
| `sldgciParau.dll` | `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce` | `0x32f70000` |

The pinned originals are AMD64 build `34.5.2.0604`. Stateless Apple LLVM 21 decodes the original instructions. Bounds follow the exception directory and complete chained unwind groups, with seven small leaves bounded by their reviewed return or tail jump. This measurement uses source bytes and numeric metadata.

## Three representations

| Representation | Meaning | Conversion owner |
| --- | --- | --- |
| `FACE_ID_2001` pointer field 1 | Actual runtime external file/configuration owner pointers supplied by the entity-id representation | `makeFaceIdAttribute`, then explicit pointer repair or list restoration when selected |
| Integer field 3 | Auxiliary face ID followed by signed owner mirrors | Model helper `+0x20` reads `moExtObject_c.f78` and `+0x10` resolves a mirror |
| Temporary pointer-sized list representation | Signed `-1` for the actual local owner, otherwise an ordered external-owner list index | `mo_genAttribList` versus `mo_resetAttribList` / `mo_assignAttribList` |

The temporary conversion marks the current owner with `-1`. The persistent mirror comes from `IndexInRefList`, and the referenced configuration has its own name and ID.

## Attribute production and the zero-branch correction

`gcFaceIdAttrib_w::makeFaceIdAttribute`, `[0x43b39bb0,0x43b39e5b)`, obtains the real entity data through the installed helper's slot zero. In the selected new-surface environment it installs the auxiliary ID in pointer field 0, real external-owner pointers in pointer field 1 and primary integer data in integer field 2. Integer field 3 contains the auxiliary ID and converted owner mirrors.

In its bounded stack-array branch, `0x43b39cd5` tests each actual owner pointer. A null pointer reaches `0x43b39d00` and emits zero. A nonnull pointer calls the backend helper's virtual `+0x20` at `0x43b39cf7`, explicitly supplying null entity context. The actual model target is `[0x4c6ce000,0x4c6ce0c0)`: it returns signed `owner+0x78` directly when nonnegative or when entity context is null. Only a negative index with nonnull entity context can enter its model/manager sharing branch.

The cited rectangle path at `0x43b39d00` proves the null-input branch. A nonnull local owner produces zero when its allocated list index is zero. The large heap-array path has a separate branch and remains outside the proven null handling. [Rectangle partition](GeneratedRectanglePartition2026.md) · [Fresh-list counter](DownstreamLocalOwnerContext2026.md)

The public `setIDHelper` at `0x43b3a800` stores the supplied helper in `0x44165d90` and forwards it through `0x43e75840`. The backend setter at `0x32f83a70` installs the same pointer in `0x3312d700`. The bridge at `0x43e746d0` resolves the backend getter `0x32f819d0`. Model helper table `0x4cdcb328` binds conversion slots `+0x10` to `0x4c6cd890` and `+0x20` to `0x4c6ce000`.

## Explicit mirror resolution

The model helper `[0x4c6cd890,0x4c6cdb92)` receives the kernel entity, an address of its signed mirror and an output owner pointer. For a face, `mo_FaceToModel` follows the actual body to its `BODY_RECIPE` pointer attribute. `mo_SetBodyModel` installs the live model pointer in that attribute.

With the new surface environment selected, the resolver creates a local external object from the model, takes the active configuration at model `+0xd78` and applies its name and ID before sharing through the FR manager. The remaining branches depend on path, title and configuration state.

Any nonnegative mirror enters the manager lookup at `0x4c6cdb11`. If the found object compares equal to the canonical local object, the resolver can use the canonical object. Missing and negative lookups fall back to that local object. Normalization can store the local index back in the mirror. The `-1` branch preserves its separate value, and missing model or manager context returns failure.

Backend helper `[0x32fa33e0,0x32fa37b0)` handles actual face or edge definitions with a nonempty integer field 3. It recreates absent pointer field 0 from the first integer. It reconstructs pointer field 1 when absent or when refresh is requested. It calls helper `+0x10` at `0x32fa36ba` for each owner mirror. Successful resolution populates the pointer array and can normalize the integer mirror. An unresolved owner aborts that branch. Helper `[0x32fa31f0,0x32fa33dc)` repairs missing pointers through a separate writeback path.

## The selected downstream getters skip that repair

| Exact actual path | Repair mode |
| --- | --- |
| `moFace::getMultiSurfaceId(wanted=0)` at `0x4be995a0` -> gcu `0x43b38ce0` -> bridge `0x43e80f80` -> backend `0x32fa2750` -> generic `0x330384d0` | Backend explicitly clears `r9d` at `0x32fa2753`: repair zero |
| `moFace::getSurfaceId` fallback at `0x4be9b241` -> gcu oldest `0x43b393b0` -> bridge `0x43e8f3c0` -> backend `0x32fa37b0` | Count query, single-attribute query and multiple-attribute query all explicitly pass repair zero |
| gcu `getSurfaceIdRep` at `0x43b393e0` -> bridge `0x43e868b0` -> backend `0x32fa2a00` | New-environment branch jumps to `0x32fa2780`, which reads existing pointer field 1 into the materialization data |

Generic `getFromEntity` at `0x33038900` calls repair at `0x330389ad` only when its third argument is nonzero. Generic `getAllFromEntity` at `0x330384d0` calls repair at `0x3303860c` only when its fourth argument is nonzero. The oldest getter's version argument controls which attribute it reads.

The materializer requires its owner pointers before ordinary downstream lookup. Upstream loading provides that preparation separately.

## Partition and serialization boundaries

The ordinary `moPart_c +0x1a58` target `[0x4c1b7600,0x4c1b7b75)` loads the partition, enumerates the returned bodies and calls `mo_SetBodyModel` at `0x4c1b7952`. The installed body model supplies the context used by owner-mirror resolution. This checkpoint pins the model attachment.

The current part serializer's virtual slot `+0x4b8` reaches `0x4c2309d0`. It calls `mo_genAttribList` with mutation disabled for ordinary nonnull bodies. The selected embedded-body paths use the in-place `-1` and list-index conversion. `mo_assignAttribList` and `mo_resetAttribList` implement the inverse operations in those paths.

The successful ordinary part load selects repair 1 with refresh 0 after attaching the body model. The next record pins the direct caller and the distinction between an absent owner array and one containing a null element. [Ordinary part reload](DownstreamPartOwnerReload2026.md)

## Replay and limits

Use [VerifyRuntimeOwnerSources.py](../../tooling/sw2026/downstream/VerifyRuntimeOwnerSources.py) with `--bin-directory` pointing to the unchanged licensed originals, `--record` pointing to the numeric ledger and an unused `--output` path. It checks only original source identities, spans, complete exception groups, imports and virtual cells. It never loads a DLL or parses a CAD document.

Native receive, construction and save/reopen remain qualification steps. [Index-zero behavior](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/ZeroOwnerMirrorIsNotNullPointer.md)

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and [RE playbook](../../Playbook/README.md) govern subsequent generation and oracle measurements.
