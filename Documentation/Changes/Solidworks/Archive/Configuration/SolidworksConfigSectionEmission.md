# SOLIDWORKS configuration section emission

The shared archive emitter writes ordinary version-19000 part section frames
with lengths computed from their typed bodies. Direct model-header references
reserve ordered slots in the existing stream map. Later sections can use those
slots without writing a second copy of the referenced object.

The empty ghost manager derives its count from the supplied rows and stores
the signed four-bit flag separately in the same word. The emitter refuses
alternate section conditions, unsupported owners, misbound header aliases,
populated ghost rows and flags outside their native domain.

Separate guarded writer and reader processes compare two authored graphs,
three ghost settings, and eleven write refusals. Two authored ghost records
match the exact eight-byte observations in the pinned L1 and Concave files.
Complete Config-0 composition and native file admission have separate exits.
[Format record and reproduction](../../../../../re/solidworks/records/ConfigSectionEmission2026.md)
