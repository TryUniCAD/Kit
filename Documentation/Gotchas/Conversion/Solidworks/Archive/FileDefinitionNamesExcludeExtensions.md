# File-definition names exclude extensions

A 2026 shared file definition keeps two different strings: the full supplied
reference path at native member `+0x18`, and its filename stem at `+0x10`.
Using a complete filename for both members omits the native path setter's
derivation.

Static `sldarchiveu.dll!0x31a01ae0` calls Windows `_wsplitpath`, interns the stem
into `+0x10`, and retains the supplied path at `+0x18`. Serializer
`0x319fe940` writes path then stem through separate typed `moCStringHandle_c`
objects for the 2026 format. A document's display name is a separate semantic
owner and must not silently replace either field.

Derive the stem with Windows path semantics from the generated reference path.
Keep the referenced generated document's creation time explicit. Do not copy a
saved path, stem, timestamp or stock filename. The
[construction record](../../../../../re/solidworks/records/AssemblyConstruction2026.md)
contains the exact module digest, category mapping, initial-file profile and
remaining graph obligations.
