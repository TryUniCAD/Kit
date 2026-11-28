# Mate anchors and solve status have independent fields

`moReference_c.f408` stores whether the user fixed the occurrence.
`moReference_c.f400` stores its current solve status. Native construction
starts both occurrences at solve status `3`. The three disclosed
solved assemblies store `4` for their fixed occurrence and `3` for the
floating occurrence.

Apply the authored fixed flag to `f408` when constructing a cold
assembly. Measure the solver's transition separately during native
qualification.

[Native factory and save evidence](../../../../../../re/solidworks/records/PlanarMateWrapperWriteState2026.md#fixed-occurrence)
