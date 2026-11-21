# SOLIDWORKS 2026 direct configuration sheet-metal master

B04-SW2026-CONFIG-SHEET-METAL covers the directly owned empty
`moSheetMetalMaster_c@1` record in ordinary resolved part Config-0.
It contributes to the full configuration walk in
[PR #183](https://github.com/TryUniCAD/Kit/pull/183).
Its immutable extraction reference is
[`a7c48f805262e5147f3aebb9cf792b87b24b5b0e`](https://github.com/TryUniCAD/Kit/tree/a7c48f805262e5147f3aebb9cf792b87b24b5b0e).
The bounded read and store entry points use the same shared archive
executor as the other configuration owners. Both take the caller's
actual inherited part identity and active archive map. Their call
sites in this slice are the guarded archive observations. The normal
SDK part registry and conversion paths retain their prior scope.

## Native ownership and rules

The exact static analysis binds SOLIDWORKS 2026 SP05.2 build
34.5.2.0604. The resolved part path at `sldmodu.dll!0x4c234150`
selects the directly owned `f1018` body in the part branch for a
nonzero `f1014` (since archive version 0x10ec). The predecessor module
SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The installed `sldsmmu.dll` SHA-256 is
`460e6d82f6b811805860b6df03e7b551a4a573aad598bd27501226586b0c9b95`.
Its registered constructor at `0x3d8dddc0` binds vtable
`0x3d9cca88` slot `+0x2c8` to `0x3d8e30b0`.
[Pinned static evidence](https://github.com/TryUniCAD/Kit/blob/a7c48f805262e5147f3aebb9cf792b87b24b5b0e/re/solidworks/records/SmmMasterArchive2026.json)

The body dispatches its `moFeature_c` base in its concrete
lightweight, resolved and XML contexts. It then reads a signed
32-bit `n370` at archive version 19000. On store, the number of
`f358` items governs this field. The physical positive has four
null base object fields and empty inherited lists. A nonempty
sheet-metal body list would dispatch `moPerBodySheetMetalData_c`
members. Their layouts and populated inherited object links retain
separate qualification.

## Physical and guarded controls

The committed source is the disclosed
[`CircularProperties.SLDPRT`](../v2026/corpus/part-properties/CircularProperties.SLDPRT)
from [`601289d81cfdf429a0be0ea6f4ee84545122c2a9`](https://github.com/TryUniCAD/Kit/blob/601289d81cfdf429a0be0ea6f4ee84545122c2a9/re/solidworks/v2026/corpus/part-properties/CircularProperties.SLDPRT).
Its file SHA-256 is
`1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23`.
The prior [field-modes receipt](../measurements/2026/ConfigFieldModesSource01.json)
pins both original streams and the native owner interval.

| Control | Part flag `f1014` | Owner interval | Incoming and outgoing map | Final Config map counter |
| --- | ---: | --- | --- | ---: |
| CircularProperties | 1 | [25324, 25473) | base 4, counter 119, 118 members | 122 |
| L1 | 0 | absent | absent owner | 110 |
| ConcaveOwned | 0 | absent | absent owner | 94 |

The [full traversal](../measurements/2026/ConfigSheetMetalTraversal01.json)
uses an isolated copy of the pinned aggregate SDK, captures the true
enclosing part at slot 2, and compares the identity of each incoming
map entry before and after the direct body. The first three entries
are the part class, its instance and the actual ModelHeader-derived
alias. The bounded main process recovers those same anchors through
`ReadPartStart` and sets the measured checkpoint counter. It requires
no reference to slots 4 through 118 because the body is link-free.
It verifies all typed fields by the digest from the full physical
trace and re-emits the exact interval.

The independent wire case uses an authored model, signed fields and
Unicode. An outer cursor starting at 7 reaches 162 for a 155-byte
body. New map allocations, inherited links, wrong class, mapped
master, wrong part, incompatible archive version, truncation,
trailing data and signed nonzero body counts refuse in the tested
paths. Rejected direct actions leave the tested cursor, model field
or output buffer and original map unchanged.
The same process checks enabled, disabled and invalid flag targets
through the shared virtual field executor. It also refuses the
six-byte encoding of each of the four otherwise null object fields
and independently authored six-byte zero counts on read and write.
The accepted body keeps both the null tags and the inherited empty
list count in their measured two-byte forms.

A third process builds an independent complete typed map with
occupied slots 1 through 118, including 30 class entries and
88 object entries. Its base is 4 and its counter is 119. Both bounded
operations preserve each entry identity and both inverse lookups,
verified immediately after each operation. This case uses the
authored body. The pinned aggregate traversal remains the evidence
for the actual native 118-entry map.

```sh
python3.14 -I -B re/tooling/sw2026/TraceCfgMaster.py
python3.14 -I -B re/tooling/sw2026/CheckCfgMaster.py native
python3.14 -I -B re/tooling/sw2026/CheckCfgMaster.py wire
python3.14 -I -B re/tooling/sw2026/CheckCfgMaster.py full_map
```

The physical trace requires the pinned aggregate Git object. All
three [guarded replays](../measurements/2026/ConfigSheetMetalBody02.json)
ran in fresh processes against the scoped SDK with zero runtime
external accesses. The [initial replay receipt](../measurements/2026/ConfigSheetMetalBody01.json)
preserves the earlier two-process evidence. The queue regression
covers all three current cases. These observations qualify the
typed wire rule. Native CAD
execution, held-out qualification, populated sheet-metal serialization
and whole Config-0 admission retain separate evidence requirements.

## Populated master follow-up

The direct owner's ordinary read and store scope ends at an empty
`f358` list and null inherited links. The signed `n370` count and the
typed object-pointer framing of the populated list have static
evidence. Concrete per-body serialization remains open.

The exact 2026 corpus report includes 88 complete Config stream
replays. The pinned research grammar knows the outer repeat and
checks each nonnull child's class. The accompanying registry has no
concrete `moPerBodySheetMetalData_c` schema. The report gives no
positive per-body observation or per-master count inventory.
[Corpus receipt](https://github.com/TryUniCAD/Kit/blob/fe592b8e7a4922dccf8298541453baf41d60b001/re/solidworks/measurements/2026/BinaryArchiveCorpusAfterHistory01.json) ·
[Pinned research grammar](https://github.com/TryUniCAD/Kit/blob/698fa68a6a9990bc4c125d2fea36c3e443a14445/re/tooling/sw2026/serial/defs/SmmMaster.py)

The recorded populated-master contrast injects an exploded-view
object into a typed research model to test refusal. The first
separate prerequisite for genuine sheet-metal history is an
ordinary exact-build save with one observed nonnull body pointer
and a second save with varied body membership. Bind the concrete
per-body descriptor, field order, allocation or alias behavior
and linked topology owners before admitting the positive list.
The counted-row and map primitives are already shared. A populated
direct body that allocates child slots would additionally require
an exact measured map handoff. Full parametric acceptance then
requires independent native rebuild and edit evidence.
[Refusal contrast](https://github.com/TryUniCAD/Kit/blob/fe592b8e7a4922dccf8298541453baf41d60b001/re/tooling/sw2026/throughsource/ProveStockTree.py#L76)

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Reverse-engineering playbook](../../Playbook/README.md) ·
[Direct owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/DirectSheetMetalOwner.md) ·
[Canonical widths gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/DirectMasterWireWidths.md)
