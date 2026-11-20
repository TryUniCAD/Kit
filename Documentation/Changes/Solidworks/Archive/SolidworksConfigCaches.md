# SOLIDWORKS configuration cache records

The internal `ReadCfgCache` decoder accepts the ordinary version-19000
part's bounded mass and empty bounds records. Supply the exact field
interval and the mapped schema-one part owner with its current archive
map snapshot. Mass slots retain their atom rows, inline property values
and the signed trailer read after two slots. The decoder requires full
interval consumption and retains the caller's map.

Disclosed part files cover zero, one and two physical slots. A separate
authored frame exercises two atom rows, both string encodings and a
distinct signed trailer. The fresh process checks also exercise
truncation, framing and owner refusals. Populated bounds records require
additional owner layouts. Queue execution and full physical `Config-0`
admission are pending.
[Source record and process commands](../../../../re/solidworks/records/ConfigCacheSlice2026.md)
· [Mass cache trailer gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Configuration/MassCacheSelectorFollowsTwoSlots.md)
