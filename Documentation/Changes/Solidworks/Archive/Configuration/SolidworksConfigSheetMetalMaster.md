# Direct configuration sheet-metal master

`ReadCfgMaster` and `WriteCfgMaster` consume and emit the directly owned
schema-one sheet-metal master within an ordinary SOLIDWORKS 2026 part.
The caller supplies the bounded `f1018` body, its inherited part node and
the linked archive map. Shared feature fields and native virtual
dispatch handle the inherited body. The signed body count derives
from the modeled sheet-metal body list.

The current scope requires an empty body list, empty inherited lists
and null object links. The direct master has its own concrete type
and consumes bytes without taking an archive slot. Populated body
orders, other resolved contexts and full Config-0 admission retain
separate exits.

A guarded process exactly re-emitted the 149-byte physical
`CircularProperties` owner with all typed fields and the inherited
map preserved. Another process emitted an independently authored
155-byte record and checked malformed owner, count and framing cases.
The queue regression uses these same process boundaries.
[Evidence and reproduction](../../../../../re/solidworks/records/ConfigSheetMetalMaster2026.md)
