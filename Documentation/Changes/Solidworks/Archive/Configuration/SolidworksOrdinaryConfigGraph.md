# Complete ordinary SOLIDWORKS part configuration graph

The shared archive codec reads both physical sections of the measured
format-4, version-19000 part Config-0. It retains the actual ModelHeader
objects and configuration map. Its writer derives the section lengths,
map entries and stream contents from the typed graph.

Four disclosed process probes reproduce the complete streams byte for
byte. They check map identity, section boundaries and truncation and
ownership refusals. A separate guarded process covers exact presence
bytes, signed empty repeats and inline sheet-metal ownership without
new CAD fixtures. The complete reader is an internal prerequisite for
literal part property validation and the scoped native part composer.
Public transfer, assembly profiles and fresh native acceptance each use
separate evidence.
[Scope, source hashes and reproduction](../../../../../re/solidworks/records/OrdinaryPartConfigGraph2026.md)
