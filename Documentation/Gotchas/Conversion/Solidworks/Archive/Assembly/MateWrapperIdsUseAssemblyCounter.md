# Resolved mate wrappers consume an assembly-wide counter

The first two resolved wrappers in A17 have `f78` equal to their
endpoint ordinal. The assembler assigns `f7c` from that ordinal and
independently takes each fresh `f78` from the owning assembly counter.
It advances and persists that counter in Config-0 as `fd48`.

Use the next model-local wrapper ID when attaching a resolved selection.
Already assigned wrappers retain their IDs. The detached view-only
wrappers are outside the traversal and keep their unset state.

[Native traversal and disclosed receipt](../../../../../../re/solidworks/records/CoincidentMatePublication2026.md#wrapper-ids-consume-a-separate-counter)
