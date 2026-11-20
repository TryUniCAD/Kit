# SOLIDWORKS scene user-property fields

The internal version-19000 layout for the shared user-property bag
keeps the signed physical count, each ordered kind, and the corresponding
binary32, signed integer or CString value. The shared field program
rejects kinds greater than two at the stored kind word before interpreting
a value or reading a later owner.

The disclosed one- and two-directional-light controls and populated
property control each re-emit six linked streams byte exactly in memory.
The independent wire comparison reads the actual 48-byte populated bag.
Three variants with an unsupported kind refuse at the expected typed
boundary. Public scene projection, writer qualification and general
application getter parity remain separate.
[Format and native evidence](../../../../../re/solidworks/records/SceneLightCounts2026.md)
