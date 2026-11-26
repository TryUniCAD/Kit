# Counted SOLIDWORKS archive body rows

The archive field layer can read and write ordered rows through explicit
field rules and callbacks. Each row gets its own field scope and index
while retaining its parent scope and actual field mapping. Count readers
use the rule's vendor, framework, split or fixed-width wire format.
Rejected prefixes leave the reader cursor and fields at the previous
state. Count writers compute lengths from the rows and retain equivalent
source count words and valid accepted widths.

The [process integration](../../../tests/Convert/Solidworks/ArchiveRows/CountedRowTests.py)
checks independent wire bytes, computed count overlays, row ownership
and complete consumption. The
[escaped-width case](../../../tests/Convert/Solidworks/ArchiveRows/CountWidthTests.py)
checks an explicit vendor count and an inline framework count across
fresh read and write processes. The
[read refusals](../../../tests/Convert/Solidworks/ArchiveRows/RejectRowTests.py)
check truncation, repeat limits and cursor rollback. The
[write refusals](../../../tests/Convert/Solidworks/ArchiveRows/RejectWidthTests.py)
check invalid width constraints and count modes. Current-revision
process results await remote CI.
[Scope, ownership and rules](../../../re/solidworks/records/CountedBodyRowSlice2026.md)
