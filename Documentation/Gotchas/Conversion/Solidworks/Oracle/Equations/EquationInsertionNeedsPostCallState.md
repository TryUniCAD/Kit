# Equation insertion needs post-call state

The first ordinary global-assignment author expected Add2 to return the requested row index. The exact 2026 call instead returned -1. Its observer stopped immediately, leaving post-call row count and publication unknown. Both pristine controls were healthy and no native source was saved. Older official API pages also differ about the integer return convention.

Do not infer success or failure solely from that return. Preserve it, capture actual count and row/owner state before evaluation, record evaluation and inspect the state again. Require real dimension values, dependency edits, geometry, diagnostics and persistence for source qualification. Keep any extra evaluation call explicit. The [bounded successor record](../../../../../../re/solidworks/records/EquationAdd2Publication2026.md) does this without changing the equation input or grading a result that has not been observed.
