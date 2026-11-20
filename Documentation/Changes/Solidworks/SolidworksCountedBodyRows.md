# Counted SOLIDWORKS archive body rows

The archive field layer can read and write ordered rows through explicit
field rules and callbacks. Each row gets its own field scope and index
while retaining its parent scope and actual field mapping. Count readers
use the rule's vendor, framework or fixed-width wire format. Count
writers compute lengths from the rows and retain a supplied count word
when its interpreted value agrees with that length.

The [process integration](../../../tests/Convert/Solidworks/ArchiveRows/CountedRowTests.py)
checks independent wire bytes, computed count overlays, row ownership
and complete consumption. The [refusal cases](../../../tests/Convert/Solidworks/ArchiveRows/RejectRowTests.py)
cover a truncated framework escape and an oversized repetition.
Current-revision process results await remote CI.
[Scope, ownership and rules](../../../re/solidworks/records/CountedBodyRowSlice2026.md)
