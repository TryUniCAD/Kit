# SOLIDWORKS assembly VisualStates composition

A bounded research composer builds the parent `VisualStates` stream from
two ordinary assembly occurrences, their actual configuration and authored
display states. The parent uses context flag zero. Explicit creation times
on the three principal planes match their ResolvedFeatures and VisualStates
owners on reread.

Two independent neutral parents produce 1,393 and 1,615 stream bytes with
terminal maps 38 and 39. Each typed read re-emits the complete store with
zero raw fields or unread tail. Construction reads zero files. The two
containers also carry the computed display list with the same names and
visibility. Native loader acceptance, child appearance and the relationship
between the distinct display stores remain open.

[Construction record](../../../../../re/solidworks/records/ConcentricVisualStateStore2026.md)
· [Guarded receipt](../../../../../re/solidworks/measurements/2026/ConcentricVisualStateStore01.json)
