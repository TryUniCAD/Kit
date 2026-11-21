# A cache warning can leave no rebuild pending

The generated attached rectangle opened with warning 32, zero reported
bodies and `NeedsRebuild2=0`. Its cache-free twin opened at the same path
with one body and no warning. Explicit rebuild recovered the correct
solid in the attached candidate, and the controls passed.

Measure initial body count and open warnings independently of
`NeedsRebuild2` when qualifying a cache. The bridge enumerates the
partition's bodies after kernel receive and before model attachment.
That count can distinguish a receive problem from later attachment
behavior in a controlled trace.

[Native open receipt](../../../../../../re/solidworks/measurements/2026/GeneratedRectangleAttachmentNative04.json)
and [partition receive trace](../../../../../../re/solidworks/records/PartitionReceive2026.md).
