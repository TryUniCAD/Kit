# SOLIDWORKS square revolve sketch relations

The strict SOLIDWORKS reader preserves the ordered equal length relation on
the two distinct adjacent contour edges of an ordinary square revolve. It
checks the local line handles, reference counts and solved lengths. The
selected construction axis remains a separate entity.

The shared revolve constructor accepts an explicit neutral `equal` constraint
on those edges and builds the logical relation and both line handles. The
construction record has no driving value. Geometry alone never creates the
equal length relation. The normal writer accepts the qualified partial
Mid Plane and Two Directions square profiles.

Two disclosed SOLIDWORKS 2026 SP05.2 controls establish the embedded
`sgLogG2Dim` format. Two additional native originals were locked before the
constructor change. Two generated disclosed archives preserve the ordered
owners and replay twenty typed streams with zero worker file reads. Both
independent cases pass native comparison with zero rebuild errors and
warnings, live angle edits, and fresh reopen.
[Record and lock](../../../../../re/solidworks/records/RevolveEqualLengthRelations2026.md)
