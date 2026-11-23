# An exploded-view manager can have a clock without a revision log

The disclosed SOLIDWORKS 2026 D01 assembly and its edited save both
store an empty `moExplViewManager_c` through the assembly's `f1590`
owner. It has a nonzero 100 ns FILETIME in `f2a0/f2a4` and no
`moLogs_c` entry in either Header. The model root has the reciprocal
shape: its own revision log and no feature FILETIME.

Derive revision membership from the actual Header log and its typed
persistent owner. Read feature instants independently from typed
feature nodes. A single guessed creation ledger would either invent
a manager log or omit a real feature timestamp. The
[D01 chronology record](../../../../../../re/solidworks/records/ConcentricD01AssemblyChronology2026.md)
links the exact original and edited Header comparisons.
