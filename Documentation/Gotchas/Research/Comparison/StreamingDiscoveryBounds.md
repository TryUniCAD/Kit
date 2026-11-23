# Discovery limits must apply during enumeration

## Expectation

A directory-entry limit should bound discovery before a large export tree is retained in memory.
A selective document pattern should not require materializing every unrelated sidecar first.

## Observed boundary

The earlier bulk discovery used `os.walk` and checked the limit after each yielded directory.
Python creates that directory's file and folder lists before yielding them.
A large flat directory could therefore be fully enumerated before the configured refusal.
The selected-file limit alone did not bound this preliminary work.

## Current behavior

Discovery now consumes `os.scandir` entries incrementally.
The input root and encountered entries consume the discovery budget before further retention.
Selected files retain their separate limit.
Linked directories, linked selected files and enumeration errors remain refusals.

Keep unrelated receipts outside the selected document pattern.
Do not interpret a discovery refusal as a completed comparison.
The filesystem can perform its own buffered reads; this bound governs the programme's entry accounting and retained work.

See the [bulk procedure](../../../Tasks/CompareDecodedDocuments.md)
and [follow-up change](../../../Changes/Research/Readers/Comparison/BulkComparisonFollowups.md).
