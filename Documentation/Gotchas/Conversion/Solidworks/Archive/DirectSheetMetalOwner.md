# A direct sheet-metal master consumes an untagged body

Counting every concrete body as a tagged graph object advances the
Config-0 archive map too early at the sheet-metal master. On the
disclosed SOLIDWORKS 2026 SP05.2 circular part, `f1014=1` selects the
149-byte `moSheetMetalMaster_c` at `moPart_c.f1018`. Both sides of the
body have map base 4 and counter 119. L1 and Concave use `f1014=0` and
have no such body.

Execute the inherited feature schema with the master's own concrete
virtual targets and preserve the incoming map in the empty-body
profile. The existing zero-wire `Direct` action serves a different
field role that introduces real map aliases.
[Physical traversal](../../../../../re/solidworks/measurements/2026/ConfigSheetMetalTraversal01.json)
