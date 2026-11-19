# Ordinary part load explicitly repairs absent face-owner pointers

The ordinary part partition-load path restores absent face owners after installing the body's model. The face getter reads the resulting pointers. [Pointer and mirror rules](DownstreamRuntimeOwnerPointers2026.md)

Task `B04-SW2026-DOWNSTREAM-RUNTIME-OWNER`, owner `flag_ownership`, delivery PR #121. Root owns integration, the generated candidate and native qualification.

## Exact selected route

The three exact `34.5.2.0604` originals supply eleven complete functions, seven declared unwind fragments, eleven instruction windows, five virtual cells and eight imports. Small leaf bounds end at the actual return or tail jump. [Numeric record](DownstreamPartOwnerReload2026.json)

| Edge | Source-bound behavior |
| --- | --- |
| Actual `moPart_c` table `0x4d1252d8 + 0x1a58` | Calls `[0x4c1b7600,0x4c1b7b75)`, SHA-256 `8b1f0fb8530dc217fd14fdc65cd7a1e62db8b4083fddc3e9b7478891fd212d3e`. |
| Named-partition selection | The outer version must be at least `0xb90`. Virtual `+0x1a70` calls `0x4b286ea0` and reads part `+0x13c8`. Its nonzero branch attempts the named partition load. |
| Successful load | Installs the nonnull partition at `0x4c1b7879` and enumerates its bodies. |
| Model attachment | Each actual body is cleaned, automation attributes are removed, and `mo_SetBodyModel(body, actual part)` runs at `0x4c1b7952`. |
| Explicit preparation | `0x4c1b797a` calls actual imported `gcAttrib_w::getAllFromBody(body, NULL, &array, 1, 0)`. The last arguments are repair 1 and refresh 0. |
| Actual public/backend join | `0x43a1a870` calls `0x43e80e60`. IAT `0x43f5d598` resolves backend `gciAttrib_w::getAllFromBody` at `0x33038380`. The bridge preserves repair 1 and refresh 0. |
| Repair invocation | Backend `0x3303849f` calls `[0x32fa33e0,0x32fa37b0)` with the actual body and returned attribute array. Actual face/edge definitions are selected inside that helper. |

The repair receives the body model already installed in `BODY_RECIPE`. The model helper resolves the active part, configuration and FR manager from that owner.

## Exactly what `(process_face_id, 0)` means

The repair follows this sequence.

1. Integer field 3 must exist with a positive count. Its first element recreates pointer field 0 when that pointer-values field is absent.
2. Pointer field 1 is queried independently at `0x32fa3623`. A positive pointer count with refresh 0 bypasses owner-array replacement at `0x32fa3630`.
3. If replacement is needed, `0x32fa3641` initializes owner index `j=1`. The loop runs while `j < integer_field3_count`.
4. A two-integer field `(process_face_id, 0)` has one owner iteration, using element 1 as mirror zero.
5. `0x32fa36ba` calls the actual installed model helper `+0x10`. Successful resolution supplies the real pointer field 1 array and may update a nonnegative mirror. Failure leaves that repair branch incomplete.

A pointer-values array containing one null element has positive count. Refresh 0 skips replacing it. [Owner array count](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/NullOwnerElementDoesNotMakeAnEmptyArray.md)

For an absent runtime owner array, this caller explains the reconstruction from the integer mirror. The generated partition uses the previously pinned nontransmitted pointer-values rule. Complete receive normalization remains open. [Partition pointer transmission](GeneratedRectanglePartition2026.md)

## Local owner is conditional on the actual external index

Mirror zero is a valid indexed lookup. At `0x4c6cdb11`, the model resolver calls `[0x4bb37050,0x4bb3705b)`, which loads FR manager `+0x20` and tail-calls `moExtObjectList_c::getExtObjFromIndex` in the external-reference index domain.

The resolver first constructs and shares the local file/configuration owner. When the indexed owner compares equal, the result can canonicalize to that local object. An existing different owner is returned from the index. A failed lookup falls back to the local owner under the mirror-normalization conditions in the pointer record.

A generated local mirror zero requires a matching indexed owner or the missing-index fallback. The ordinary manager's encoded external list, runtime initialization and first local registration determine which branch it takes.

## Replay and limitations

The preceding [VerifyRuntimeOwnerSources.py](../../tooling/sw2026/downstream/VerifyRuntimeOwnerSources.py) also checks this ledger with the same `--bin-directory`, `--record` and unused `--output` arguments. It performs original-image metadata checks only.

The checkpoint measures source identity and call order. Native cache load, edit, save and reopen remain qualification steps. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [RE playbook](../../Playbook/README.md)
