# Current Fusion leaves stray bytes after the final ACT record

## Expectation

The ACT segment bulk stream ends with its final record. The final record is a `RevGUIDACTDataMany` record that holds one `revGuidMap` member. A strict reader can then reject any byte after the decoded members.

## Actual behavior

Fusion 2706.1.17 often writes a few bytes after the final ACT record. Kit's bulk slicer gives the last record every byte up to the stream end. The strict reader then raised `ValueError("Unexplained trailing Fusion entity payload bytes")`.

The native member set of `RevGUIDACTDataMany` registers only `revGuidMap`. `ACTChangeDataMany` registers no member. No native field can therefore own the extra bytes.

Repeated native saves of unchanged documents separate the record from the extra bytes.

| Document | Save | Final record fields | Extra bytes |
| --- | --- | --- | --- |
| Fresh design | First | Reference | 0 |
| Fresh design | Second | Equal to first | 0 |
| Fresh design | After reopen | Equal to first | 2, different value |
| Plane Form | First | Reference | 2 |
| Plane Form | Second | Equal to first | 2, equal value |
| Plane Form | After reopen | Equal to first | 2, different value |

The census of 72 affected local archives found these extra byte counts.

| Extra bytes | Archives |
| --- | --- |
| 2 | 68 |
| 16 | 1 |
| 26 | 1 |
| 28 | 2 |

The bytes change between saves of equal records. They may hold uninitialized memory, so treat them as private data.

## Workaround

Read every ACT record except the last one strictly. Read the last record with `ReadSlack` and keep its unread bytes in `ParsedSegment.BulkSlack`. Write those bytes back after the last record so the stream stays byte-exact. Keep the strict check for every other segment and every other record.

## Evidence

- [Slack census](../../../../re/Fusion/Reconstruction/ActSlack/SlackCensus.json)
- [Repeated native saves](../../../../re/Fusion/Reconstruction/ActSlack/Saves.json)
- [Native save probe](../../../../re/Fusion/LocalOracle/ActSlack/Probe.json)
- [Native member facts](../../../../re/Fusion/Reconstruction/ActSlack/NativeFacts.json)
- [Form document change entry](../../../Changes/Fusion/TSpline/FusionFormDocuments.md)
