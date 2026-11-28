# SOLIDWORKS configuration unit tables

The internal `ReadUnitTable` codec reads one complete version-19000
`moUnitsTable_c` object from a bounded buffer and the owning archive's
map snapshot. It returns typed unit fields and the resulting map.
`Base` fields share their concrete object's field scope. `Present`
fields retain the native scalar and use it to select the optional fields.

The codec checks the ordinary 16 unit roles and the measured optional
length override. It refuses trailing or truncated input, incompatible
descriptors and unresolved inherited class slots. Current density rows
use the absent-override profile. Full `Config-0` admission requires the
remaining configuration grammar.

Fresh host processes read three complete records from the tracked ladder
and concave fixtures. They matched the independent typed observations
and refused the malformed record and map variants. The merge queue
integration cases use the same disclosed records and wait for CI.
[Scope and verification](../../../../../re/solidworks/records/ConfigUnitTableSlice2026.md)
· [Map seed gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Configuration/UnitTablesInheritClassSlots.md)
