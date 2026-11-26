# History write results have output coordinates

A parsed History graph records the source byte positions of its nodes.
Editing a comment changes the length of the stamp and shifts the following
date-code object. The source nodes retain their original positions.

Use the graph returned by `WriteHistGraph` to locate objects in the emitted
buffer. Its map contains the nodes read from those bytes and preserves aliases
within that graph.
[Guarded comment edit](../../../../../../re/solidworks/records/HistoryStreamSlice2026.md)
