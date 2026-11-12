# Fusion history counters are distinct identities

A newly authored history often begins with equal integers, such as `4, 4`. It is tempting to treat them as a duplicated generation or size. A rolled-back native history instead stores `3, 10`. Requiring equality rejects that valid journal; writing the current value twice loses the maximum allocated state ID.

Native symbols and instructions prove that the first value is `HISTORY_STREAM` current state, the second is its maximum allocated state and the third is its retained-state limit. The fourth value comes from the entity-tag allocator, independently of those state IDs. It is not a stream ID or count of serialized history records. The native writer can emit `-1` for that fourth value under a different save option; the present typed profile requires a nonnegative allocator value and rejects that variant.

The integer within a bulletin board is also not an ordinal. Native restoration reads the enum `mainline=0`, `stacked=1`, `succeeded=2`, `failed=3`. Using an arbitrary larger number in an otherwise valid generated stream does not describe an additional board.

Use `CurrentStateId`, `MaxStateId`, `NextEntityTag` and `BoardStatus` independently. The optional maximum defaults to the current value only for callers that omit it. Preserve explicit maxima from parsed journals. Keep body keys, Design operation IDs and body generic-tag secondary IDs in their own namespaces.

The [native evidence](../../../../../re/Fusion/Reconstruction/JournalStates/NativeEvidence.json) includes binary and disassembly digests. The [feature entry](../../../../Changes/Fusion/FusionHistoryStates.md) records compatibility and the qualified two-state boundary. Current production support does not infer complete multi-state history support from a familiar initial topology count.
