# Empty configuration attachments in SOLIDWORKS 2026

The named loader `moModel_c::loadAttachment` in `sldmodu.dll` at
`[0x4b585d50,0x4b585fb3)` appends the `-Attachment` suffix at
`0x4b585e08`. If the storage-mode setup or named-stream open fails,
control bypasses archive construction and the object read, reaches
storage cleanup at `0x4b585f24`, and returns the current pointer at
model offset `0x7d8`. A version-gated follow-up at `0x4b585f7e`
requires that pointer to exist. The shrink-wrap path is outside this
observation.

For an opened stream, the loader calls the typed `moAttachment_c`
archive extraction operator at `0x4c2126a0`. The ordinary archive branch
uses `su_CArchive::ReadObject` at IAT `0x4cd3d890`; database mode
uses a distinct archive routine. The matching insertion operator starts
at `0x4c2140b0`. Thus the two zero bytes in the three
[ordinary discovery sources](../v2026/corpus/assembly-synchronized/Manifest.json)
are the ordinary null object marker, not a count of attachments.

These addresses refer to the build 34.5.2.0604 module with SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The [two generated empty candidates](../measurements/2026/EmptyAssemblyNative01.json)
omit the attachment stream and 31 other native streams, and match the
empty native control through save and fresh reopen. This result does not
permit dropping attachment data that exists in a populated input.
