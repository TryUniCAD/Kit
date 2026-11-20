# Ordinary SOLIDWORKS thread and partition mark records

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-THREAD-MARK` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target branch `codex/solidworks-config-thread-action` |
| Preparation base | `0cd540e298655e091bcfb4a984ba50e793d67c53` |
| Prerequisite | [Bounded feature owners and field actions](ConfigFieldActionsSlice2026.md) |
| Exit | Actual native member and map handoffs, authored signed Boolean and mark contrasts and refusals in the merge queue, then current revision review |

## Exact native scope

The disclosed files use archive version 19000 on the current ordinary
SOLIDWORKS 2026 SP05.2 `34.5.2.0604` layout. The native runtime
descriptor exports declare file schema one for both new roles. The
exact model module SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
[Runtime descriptor evidence](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ConfigRuntimeDescriptors2026.json)

The schema-one `moCThreadRefMgr_c` serializer uses vtable
`0x4cdcb848` slot `+0x28` and spans `[0x4b2e57a0,0x4b2e5bf2)`
with SHA-256
`8fcce420856a4010990b7ba39f15415d72252cf59953fa329f4a127796c2a865`.
After the ordinary zero-byte base, it reads the signed map count, each
key and unsigned holder count, and the holder links. The final signed
32-bit `f1a0` word is present above archive version `0x3755`.
Native load derives its runtime Boolean by testing nonzero. The
shared codec retains `f1a0#wire` alongside the runtime value. The
bounded reader admits an empty map or an absent manager. Nonzero map
counts and linked holder rows need further qualification, including
the separately identified native store filter.
[Thread manager order and normalization](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/CommonPartOwners2026.md#thread-reference-manager)

The schema-one `moPMarkRecord_c` serializer uses vtable
`0x4d17e9a8` slot `+0x28` and spans `[0x4bb1a840,0x4bb1a8b9)`
with SHA-256
`9c304975ba308185c5d0278a791fbae60914456cd1231096b84428db6a6142ad`.
Its single signed `f18` word carries the kernel mark ID. The two
observed files give separate stored IDs and archive slots. The reader
keeps the supplied mark word and allocates independently in the
owner's live map. The bounded mark role requires a concrete owner.
[Partition mark read and native ID ownership](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/OrdinaryPartPartitionLoad2026.md#kernel-marks-are-not-persistent-node-ids)

## Disclosed wire observations

The [source manifest](../measurements/2026/ConfigThreadSource01.json)
pins the tracked part and complete Config-0 stream identities,
physical intervals and the aggregate code digests. The reference
checkout at `5e0d5127e09de3b1646b9c662757e783cf7b4f3c` retained
the relevant archive, header and configuration read paths from
`f4fc8744235448c0ff6048e4447440bb7927a6d1`.

| Control | Part field | Half-open interval | Map counter | Physical evidence |
| --- | --- | --- | --- | --- |
| L1 boss | `fe38` | [25016, 25041) | 103 to 105 | Class 103, object 104, mark ID 3 |
| L1 boss | `f12d0` | [25101, 25132) | 106 to 108 | Class 106, object 107, empty map, Boolean word at [25128, 25132) |
| ConcaveOwned | `fe38` | [22548, 22573) | 91 to 93 | Class 91, object 92, mark ID 2 |
| ConcaveOwned | `f12d0` | [22633, 22635) | 94 to 94 | Exact null tag |

The process reuses decoded relation and color map membership, then
checks the sketch block manager, mark, thread manager and exploded
view manager in physical order. It retains each earlier materialized
map entry by identity and applies the observed counter at each
boundary. Intervening unused slots remain unmaterialized. The exact
two-byte null branch opens no body or Boolean field. The fixture
hashes bind their context before the in-memory read guard starts.

Independent authored thread records reuse the L1 thread descriptor
at slot 106. They retain the original signed words and decode runtime
values for zero, a noncanonical positive word and both signed extremes.
Each creates one distinct object in a fresh branch from the verified
map. The independently authored partition record uses the L1 mark
descriptor at slot 103 and a signed `f18` word of `-17`. Its six bytes
allocate one distinct mark at slot 105 and retain the original mark
at slot 104. This contrast verifies signed archive decoding and map
identity. Native kernel resolution and geometry semantics remain open.

Refusals cover missing descriptors, schema and role mismatch,
a borrowed root, a missing required mark, incomplete frames,
unsupported versions and unqualified map populations. The populated
holder case uses the actual earlier partition mark as its inherited
alias and must still fail the thread scope guard.

```sh
python -I -B re/tooling/sw2026/CheckCfgThread.py ladder
python -I -B re/tooling/sw2026/CheckCfgThread.py concave
```

The new guarded process cases await queue execution.
[New queue cases](../../../tests/Convert/Solidworks/Configuration/CfgThreadTests.py)
The reference observations establish the specified wire fields and their
owners. Populated thread maps, native mark-to-kernel resolution, full
Config-0 admission, neutral construction and native writing remain open.

The previously measured full ordinary pair still needs shared
`BBoxCache`, `Context`, `Direct`, `GhostCount`, `MassCaches`,
`Normalize` and `Section` actions, in addition to wider branch
semantics and the model, annotation, scene, view, material and header
link closure. The light owners also reach `Boolean` and
`Normalize` in both observed parts. Their presentation and property
owners require a separate bounded admission.
