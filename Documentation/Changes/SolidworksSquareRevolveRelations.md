# SOLIDWORKS square revolve sketch relations

The strict SOLIDWORKS reader preserves the ordered equal length relation on
the two distinct adjacent contour edges of an ordinary square revolve. It
checks the local line handles, reference counts and solved lengths. The
selected construction axis remains a separate entity.

The shared revolve constructor accepts an explicit neutral `equal` constraint
on those edges and builds the logical relation and both line handles. The
construction record has no driving value. Geometry alone never creates the
equal length relation. Public square writing remains gated on native
acceptance.

Two disclosed SOLIDWORKS 2026 SP05.2 controls establish the embedded
`sgLogG2Dim` format. Two additional native originals were locked before the
constructor change.
[Record and lock](../../re/solidworks/records/RevolveEqualLengthRelations2026.md)
