# Saved vertices can carry automation attributes

Three of the eight actual vertices in the saved 12 mm P03 partition
have nonnull `attributes_features` references. The general Parasolid
scanner expects its first vertex reference to be null, so it leaves
these genuine records out of the roster. All three typed records
have reciprocal points and saved `VERTEX_AUTOMATION_2_2001` attributes.

Read vertex membership from the validated typed graph. Retain the
attribute owner, its definition and its type-order links. The earlier
fin-shadow repair has a different admission condition and does not
repair these omissions.
[Saved active owner evidence](../../../Changes/Research/Solidworks/SolidworksSavedActiveOwnerResearch.md)
