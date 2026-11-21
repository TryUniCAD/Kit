# Mate node flags and solve status have separate owners

The coincident mate's stored node flag `0x100` and stored solve status
come from separate native operations. The first uses the inherited node
getter and setter. The second uses the mate's solve-status setter.

Track both fields when tracing a rebuild. Use endpoint residuals, native
mate status, and rebuild diagnostics to assess a solved mate.
[Native operations](../../../../../re/solidworks/records/CoincidentMateLifecycle2026.md)
