# SOLIDWORKS 2026 Parasolid rollback mark IDs

Task `B04-SW2026-PARTITION-MARKS` moves the bounded tuple result from the
[aggregate reader](https://github.com/TryUniCAD/Kit/commit/9be8583760b74fac5d549f791fdd2b868dadba72)
onto the shared main archive parser. The accepted base is
`eec010f5d20564721d3f9a700fb1709ec1e39931`. `ReadXmtHistory` retains its
`None` success result. `ReadHistMarks` exposes the same proof's selected
`PMARK.id` and its `preceding` owner's `PMARK.id`. The zero predecessor
sentinel corresponds to a null pointer. [Adapter reference](../../../Documentation/Reference/Adapters/Solidworks.md)

## Physical owners

Both selected values come from the decompressed `deltas` payload in
`Contents/Config-0-Partition`. The header requires
`SCH_3701250_37102_13006` and the matching 3701250 delta description. The
typed `PARTITION.current_pmark` selects a mark from the stream. Its logical
`id` must agree with the `WORLD.current_id` in the paired active payload.
The existing checks require valid map identities, reciprocal predecessor
links, the witnessed linear rollback profile, a matching highest mark ID,
and ownership of the active body in the current rollback when present. The
reader verifies the stream terminator before returning either value.

| Control | Source authority | Selected / predecessor transmit slot | Selected / predecessor ID |
| --- | --- | --- | --- |
| L1 boss | [SOLIDWORKS 2026 native part](../measurements/2026/SolidworksCurrentFinOrientation01.json) with active world body 2 | 177 / 178 | 7 / 3 |
| ConcaveOwned | [Native-verified generated solid](../measurements/2026/LocalImportReadbackFixtures01.json) with a body-free active partition and separate local solid | 3 / 4 | 3 / 2 |
| Initial-only | Independently authored empty world and one mark, using known field order | 3 / null | 1 / 0 |

On L1 the mark records occur in physical order 7, 1, 3. The predecessor
comes from the selected mark's pointer. Logical IDs need not be consecutive.
The authored initial case uses independently constructed framing and a
typed active world. It establishes the reader response to an absent
predecessor.

## Verification

From the repository root, run the [guarded process probe](../../tooling/sw2026/CheckPartitionMarks.py).

```sh
python3.14 -I -B re/tooling/sw2026/CheckPartitionMarks.py measure
```

Five isolated workers pin complete source and payload hashes before
validating the delta. Four workers enter through the strict public
document reader. The archive operations run after loading the inputs and
deny file, subprocess, and external access. The L1 faults detach the
predecessor, select a different retained mark, remove the active body's
deletion ownership, truncate the terminator, or append bytes. Both entry
points raise the same recorded diagnostic for each fault.

The [one-light control](../measurements/2026/ConfigSceneCounts01.json)
retains a valid public solid with a current delta arrangement outside the
existing rollback framing. The older `example.SLDPRT` retains its public
solid with schema `SCH_3601228_36001_13006`. The shared archive API refuses
both typed histories. Whole-document digests match the accepted-base
observations for all four source documents.

The [receipt](../measurements/2026/PartitionMarkIds01.json) records source
and payload digests, logical identities, slots, control diagnostics, and
source closure hashes. The [queue case](../../../tests/Convert/Solidworks/Partition/HistoryMarkTests.py)
uses the same process entry point. These are archive-reader observations.
Feature-to-cache binding and native writing retain their separate exits.
