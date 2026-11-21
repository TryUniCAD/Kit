# Generate the empty active partition for a local import

`MakeImportHist` takes archive version 19000 and a fresh local import history
with activation followed by local body attachment. It generates the entire
`Contents/Config-0-Partition` stream and returns the activation and selected
mark IDs for the same part's archive binding. The active world has no body.
The imported feature owns its solid in the separate LocalBodies stream.
[SDK constructor](../../../src/convert/adapters/solidworks/Archive/Partition/ImportHistory/MakeImportHist.py)
· [Import storage evidence](ImportedBaseBody2026.md#separate-local-body-storage)

The constructor allocates kernel mark IDs and application delta handles
with independent fresh counters. Both start at 1. The initial kernel mark
has no associated delta. The activation and attachment events create IDs 2
and 3 with handles 1 and 2. The active world and partition root both select
mark 3. The WORLD and partition take the first two wire indices. The mark
indices count backward from the selected mark through the retained chain.
Transmission emits selected index 3, initial index 5 and activation index 4.
Forward and preceding links follow chronological order.
[Allocation and transmit grammar](EmptyPartitionGrammar2026.md#delta-records)
· [Independent handle allocation](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/History/ParasolidDeltaHandlesFollowSessionAllocation.md)

Each retained rollback writes empty new and deleted node lists and one
preceding WORLD. Its pointer and counter fields are zero. The preceding
world is alive for the selected mark and inactive for the activation mark.
Each null pointer carries the proven rollback flag. The mark header's
change counts stay zero. The preceding-state list has its own count of one.
The SDK derives schema
descriptors from the same typed WORLD, PARTITION and PMARK shapes as the
reader. The established part codec compresses each raw transmit separately.

## Offline measurements

| Segment | Raw bytes | Framed bytes |
| --- | ---: | ---: |
| Active partition | 307 | 273 |
| Delta history | 520 | 333 |
| Total across both transmits | 827 | 606 |

Two independent processes produced the same receipt. The complete stream
matches the independent fresh history generator and the full partition
streams in all four generated part containers. The ordinary records point
from the model activation field `fe38.f18` to mark 2 and from the import
feature field `f3d0.f18` to mark 3. The SDK reads both transmits and checks
the mark chain. Typed research readback re-emits the complete stream
byte for byte. [Numeric receipt](../measurements/2026/SdkImportHistory01.json)

The complete part research builder now uses the SDK history bytes and the
returned marks directly. At their original measured logical destinations
all four previously accepted imports and their 48 streams reproduce the
same bytes with zero runtime reads.
[Integrated part receipt](../measurements/2026/SdkImportHistoryPartBuild01.json)

The constructor and shared rollback encoder refuse 14 out-of-profile
requests. The checks include another archive version, missing or reordered
events, a second attachment, a preceding world with an active mark or body,
and invalid preceding-world identity or alive state. Construction and
readback performed zero guarded file reads. This evidence covers fresh
local imports. Existing native histories with allocated gaps, partition
bodies or populated rollback records require their own history rules.
[Earlier complete native lifecycle](../measurements/2026/GeneratedLocalBodyPartCompleted01.json)

## Reproduce the receipt

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/VerifyImportHistory.py
```
