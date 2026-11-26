# Counted bodies add Python stack frames

A depth limit counts open archive objects. A counted array can add a
field callback and an array reader or writer before the next object
opens. With eight live Python calls per object, 128 objects require
1,024 frames before any outer calls.

For a known one-array body, enter the array reader directly. Keep the
write depth lifetime in the node store so its body callback can run
without an extra wrapper. These paths use seven live frames per
object in the counted-row probe. Check the stack cost of other body
callbacks before adopting the same depth guarantee.
[Callback stack proof](../../../../../../re/solidworks/records/BodyValueSlice2026.md#counted-callback-stack)
[Counted depth process case](../../../../../../tests/Convert/Solidworks/ArchiveValues/CountDepthTests.py)
