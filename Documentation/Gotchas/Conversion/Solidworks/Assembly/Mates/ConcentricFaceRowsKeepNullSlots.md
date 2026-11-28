# Concentric cap references keep their null entries

The ordinary cylinder-face list has five serialized entries. The side comes first. Each of the two cap references is followed by a null object entry. The count includes those null entries.

Preserve the complete ordered list when reading or emitting the face reference. All six disclosed saves retain the same ordering through edits. Dropping a null entry changes the archive even when the three real face IDs remain. [Linked archive record](../../../../../../re/solidworks/records/ConcentricMateArchive2026.md)
