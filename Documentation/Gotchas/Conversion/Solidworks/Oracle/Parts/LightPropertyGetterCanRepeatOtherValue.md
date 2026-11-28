# A light property getter can repeat another stored value

The exact SOLIDWORKS 2026 SP05.2 trial added a Single, a signed integer,
and a Unicode string to the same directional light. Creation returned
indices 1, 2 and 3. The zero-based getter returned the integer at every
index before rebuild, after save and after fresh reopen. The native
file retained all three distinct types and values in order.

Preserve the returned indices, getter observations and original save.
Use the actual typed archive rows to check stored values when the
getter results conflict with the successful authoring calls.
[Native and archive evidence](../../../../../../re/solidworks/records/SceneLightCounts2026.md)
