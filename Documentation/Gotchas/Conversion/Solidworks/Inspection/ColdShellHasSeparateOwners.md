# Fresh open shells have separate body state

A fresh SOLIDWORKS 2026 inward shell can own a complete stock,
terminal cap and thickness even when the part has no saved partition.
In the generated rectangular case, the stock's `f528` and shell's
`f538` alias the same configuration atom. Its producer and last
modifier are populated while the body stamps are zero. The active
configuration has an empty `f450`.

Inspect those linked fields before deriving an analytic solid. A
partition stream, persisted mark, nonzero stamp or alternate
configuration owner prevents fresh reconstruction. A saved shell still
requires its own active and rollback geometry checks.
[Guarded comparisons](../../../../../re/solidworks/records/ColdOpenShellReader2026.md)
