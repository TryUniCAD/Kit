# SOLIDWORKS 2026 configuration surface-finish helper

`B04-SW2026-CONFIG-FINISH-HELPER` is an archive leaf of the #121
delivery. The delivery branch is `codex/solidworks-config-finish-delivery`,
based on accepted main `ad5cf8d9fc7b257a045369f0860fd593da0ad0a4`.
The initial preparation is `4f79ef0c09997e168143a801b0a2c91e9adf3a7e`.
It reuses the accepted character format, shared body executor and
ordinary part–ModelHeader binding. Exit requires current-revision
review and applicable CI in its separate main delivery.
[PR #121](https://github.com/TryUniCAD/Kit/pull/121)

Full Config-0 and the public property gate retain their separate
delivery.
[PR #183](https://github.com/TryUniCAD/Kit/pull/183).

## Measured wire owners

The ordinary embedded layouts use format 4, archive version 19000,
and SOLIDWORKS 2026 SP05.2 build 34.5.2.0604. The exact
`sldmfcu.dll` SHA-256 is
`af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`.
The static wire-order record has SHA-256
`f0d882ee2b420a849780ef8f2233ef0b221ee645d3582298b0023d915ba7e32a`.
[Pinned analysis](https://github.com/TryUniCAD/Kit/blob/fe592b8e7a4922dccf8298541453baf41d60b001/re/solidworks/records/AnnotationArchive2026.json)

| Layout | Exact serialize entry | Fields |
| --- | --- | --- |
| `moSFDataHelper_c` | `0x3c860010` | 32 operations. Text and typed numeric controls, font `fc0`, annotation helper `f128`, and two separate supplemental strings in the suffix |
| `moAnnotationDataHelper_c` | `0x3c855cf0` | 14 operations. Four signed settings, an option byte, font `f08`, and two independent leader field groups |
| `utCharFormat_c` | `0x3c7bfa50` | Shared character format, with one CString and 68 typed bytes |

The field order, wire types, and role boundaries are confirmed for the
observed ordinary archive profile. The helper carries no object/class
tag or allocated index in any measured role. Constructor defaults,
native runtime repair and semantic synthesis of raw options retain
their own evidence requirements. Bounded reading consumes the exact
helper interval with the actual inherited part node.
[Finish fields](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/FinishFields.py) ·
[Shared annotation helper](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/AnnHelperFields.py)

## Physical checkpoints and guarded replay

All positions below are half-open in the decompressed Config-0
stream. The prefix belongs to `moPart_c` and the detail section is
`moModel_c.fae0`. All three roles have the same layout.

| Original | `fae0.f2e8` | `fae0.f730.f260` | `fae0.f730.f268` | Incoming and outgoing |
| --- | --- | --- | --- | --- |
| L1 blind boss | [16177, 16499) | [17306, 17628) | [17628, 17950) | Base 4, counter 69, 68 entries |
| Concave import | [14626, 14972) | [15839, 16185) | [16185, 16531) | Base 4, counter 54, 53 entries |

The full physical trace of pinned aggregate
`fe592b8e7a4922dccf8298541453baf41d60b001` reads the two hashed original
archives and consumes both configuration sections. It preserves every
map entry identity across each observed interval and binds the actual
ModelHeader alias. Each finish body has separate annotation and font
sub-intervals. The body lengths differ by 24 bytes between the two
sources because each of their two font bodies differs in length by
12 bytes. The receipt records the source file, linked stream and
typed field digests for both cases.
[Physical receipt](../measurements/2026/ConfigFinishPhysical01.json)

The independent pinned traversal passes its live map and actual part to
the current bounded decoder at each of the three finish roles. The six
shared map and object type files must match the pin byte for byte. Each
guarded read and emission checks the original entry identities, slot
order, counter, base and both inverse lookups. L1 preserves 29 class
entries and 39 object entries. Concave preserves 26 class entries and
27 object entries.
[Full native-map replay](../measurements/2026/ConfigFinishNativeMap01.json) ·
[Initial replay](../measurements/2026/ConfigFinishReplay01.json)

The queue derives a complete slot directory from the two tracked saves
using only the candidate checkout. `ReadPartStart` supplies the actual
part and linked ModelHeader identities at slots 1–3. The full trace
records 37 L1 and 25 Concave object allocation tag positions after
that prefix. The queue decodes the raw canonical tag and, for a new
class, its actual schema and name with the shared 2026 codec. A class
reference resolves against the preceding class slot. No earlier object
body fields are reconstructed from these locators. For each of the
six finish checkpoints the projected and live maps agree across
every slot, with the same descriptor kinds, names, schema or index,
object indices, counter and base. The guarded codec preserves both
inverse lookups and the exact object identities in the projected map
and reproduces all 24 field and wire digests.

The independent 372-byte case encodes distinct ANSI and UTF-16 font
owners, signed fields and varied text. It preserves every slot and
inverse lookup in its separately authored 68-entry map after read
and write. Wrong version or part identity, truncated and trailing
data, and noncanonical text length all refuse.
[Allocation tag positions](../measurements/2026/ConfigFinishMapTags01.json) ·
[Queue process coverage](../../../tests/Convert/Solidworks/Configuration/Finish/FinishTests.py)

```sh
python3.14 -I -B re/tooling/sw2026/CheckCfgFinish.py ladder
python3.14 -I -B re/tooling/sw2026/CheckCfgFinish.py concave
python3.14 -I -B re/tooling/sw2026/CheckCfgFinish.py wire
```

The separate research tools require the exact aggregate Git object.
`TraceCfgFinish.py` regenerates the physical interval receipt.
`TraceCfgFinishMap.py` reports the full inherited map and its handoff
to the bounded codec for either case. Add `--tag-offsets` to reproduce
the locator list for that case.

```sh
python3.14 -I -B re/tooling/sw2026/TraceCfgFinish.py
python3.14 -I -B re/tooling/sw2026/TraceCfgFinishMap.py ladder --tag-offsets
python3.14 -I -B re/tooling/sw2026/TraceCfgFinishMap.py concave --tag-offsets
```

For the live-map trace the research lineage hydrator retrieves missing
blobs from the selected source paths in a blobless checkout. The queue
does not resolve that Git revision or run either trace tool. The
generic research CLI does not expose a Config-0 map checkpoint. All
cases used zero guarded external accesses and zero CAD launches.
Full prelude layout decoding and public configuration admission
retain their separate delivery.
[Pinned source](https://github.com/TryUniCAD/Kit/tree/fe592b8e7a4922dccf8298541453baf41d60b001/src/convert/adapters/solidworks/Archive) ·
[History hydration](../../automation/CaptureHistory.py) ·
[Candidate history gotcha](../../../Documentation/Gotchas/Git/CandidateHistoryDoesNotIncludeResearchRefs.md)

## Shared composition

The finish layout uses the same `AnnHelperFields.py` declaration as the
tolerance helper at `f118` in accepted PR #226. Git blob
`16f0fbcd76a9ca20aeee9a4e4cf61c7b7130c5fb` identifies the shared file
in both the initial preparation and the accepted base. The finish layout
imports that declaration directly.
[PR #226](https://github.com/TryUniCAD/Kit/pull/226)

Before the full-map follow-up, the physical trace and all three guarded
processes reproduced their receipts byte for byte on this base. Their SHA-256 digests are
`61d54b4964e32ece97cf65c99bb073224ab7fa6c1cc408a310bc1b868971d731`
and `ce08a6dcb41e2322ff4439957a9f3fd828e76e746f592e71f4f0be1e9fbed37e`.
The full-map worker preserves the original physical receipt, authored
worker output and all 24 scoped wire and field digests. Its additional
checkpoint receipt has SHA-256
`e5b5fedb0fd269d2ccbe8a88a0974f93903555873825000f3f60f15fb0e596bd`.
The self-contained queue reproduced the same full slot signatures
`c0b2bbf640914d05b5ce0d8ac50e9ed02294632b2b4b6f7c040d1349b30b2e89`
and `e86051175a467ba05274ee1c3a8245f60ffbfa94f73a7ca598ab2924bfd7ff2d`.
The allocation tag receipt SHA-256 is
`725d5f3530a99d2af1164de86452b72517485720f83343e1684d3b57b9d453f6`.

The open note boundary starts at `moDetailDefs_c.f4d8`.
The disclosed note helper cases have zero `n248` attachment rows.
The persisted word is u64 and its active repetition uses its signed
low dword. Populated kinds 1, 2 and 4 carry linked helper references
and still require independent observed map and target-role evidence.
[Note attachment evidence](https://github.com/TryUniCAD/Kit/blob/fe592b8e7a4922dccf8298541453baf41d60b001/re/solidworks/records/AnnotationArchive2026.md#note-attachment-count) ·
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Reverse-engineering playbook](../../Playbook/README.md)
