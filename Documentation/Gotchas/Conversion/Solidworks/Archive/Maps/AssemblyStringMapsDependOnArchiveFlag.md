# Lightweight assembly string maps depend on an archive flag

The lightweight serializer invokes the same string-map wrapper for
`f14a0` and `f14d8`. That wrapper delegates to the MFC map serializer
with bit `0x10` clear in the archive byte at `+0x20`. It returns
before moving any map fields when the bit is set.

Check the archive mode before assigning even an empty encoded count
to either map. The current measured ordinary configurations carry
two empty counts. [Pinned native wrapper](../../../../../../re/solidworks/records/AssemblyArchive2026.md)
