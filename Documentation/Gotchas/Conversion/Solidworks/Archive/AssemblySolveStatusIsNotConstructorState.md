# Assembly solve status can change after construction

A fresh assembly allocates solve status as `0`. Later native update paths
write results from active mate items or an assembly traversal. They can write
`1`, `2`, `3` or `5`. The observed active-item scan gives `5` precedence over
`2` and uses a separate predicate for `1` or `3`.

Do not emit the allocation seed as a universal saved value. Measure no-mate,
solved and conflicting source graphs separately. The
[native trace](../../../../../re/solidworks/records/AssemblySolveStatus2026.md)
records the validated call sites and the remaining state gaps.
