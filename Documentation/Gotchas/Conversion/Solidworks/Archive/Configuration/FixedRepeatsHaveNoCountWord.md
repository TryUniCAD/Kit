# Fixed configuration repeats have no count word

The ordinary version-19000 model has ten consecutive `f9f8` records.
Its field rule supplies the count. The first bytes in that interval
belong to the first record. Reading a new count word there would move
the cursor into the record and misalign the following fields.

Use the fixed count from the owning field rule and the existing
repeat bounds. For a named repeat, obtain the count from its earlier
decoded field.
[Observed interval and verification](../../../../../../re/solidworks/records/ConfigFieldModesSlice2026.md)
