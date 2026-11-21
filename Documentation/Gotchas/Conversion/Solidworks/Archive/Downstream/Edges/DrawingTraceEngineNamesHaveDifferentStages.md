# Identically named drawing trace engines expose different stages

The original aggregate-only `re/tooling/sw2026/DrawingSaveAggregateDbgEng.py` and the staged-return `drawing_doc_return/DrawingSaveAggregateDbgEng.py` are distinct source closures. The latter provides `arm_breakpoint`, staged waits and verified per-stop ownership used by the properties restoration subclass. The former must not be selected merely because its basename matches.

A pre-event7 drawing-edge trace must also replace the original event7-only stop predicate explicitly. Removing that predicate without a paired owned SaveAs/event chronology is not equivalent evidence. Bind the exact return-engine source hash and its helper hierarchy, use an isolated flattened tool directory and fresh worker, and keep both the event ordinal and source stop timing. The [two-stop protocol](../../../../../../../re/solidworks/records/DrawingEdgeCacheTwoStop2026.md) leaves the selected edge/ID join and native execution pending.
