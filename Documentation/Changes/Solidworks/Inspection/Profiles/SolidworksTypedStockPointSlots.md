# Typed stock sketch point slots

The SOLIDWORKS 2026 reader preserves sparse native endpoint slots in closed line contours. For an axis-constrained rectangle with no driving lengths, the neutral sketch exposes four live lines and their four actual unary relations. It puts inactive point and line records in sketch attributes. The active dimension owners determine which sketch parameters are exposed.

The ordinary strict part reader was checked against three disclosed blind-cut sources. The shared sketch reader was also checked against six through-all source and edited saves. All 18 fresh processes matched the native endpoint identities and coordinates. The six linked streams in each process re-emitted byte-for-byte. The regression also checks rejection of an invalid inactive marker and a live line pointing to a retired slot.

This change qualifies the measured stock sketch read. Through-all feature construction, full readback and held-out acceptance remain open.

See the [field and ownership record](../../../../../re/solidworks/records/StockPointSlots2026.md) and [process receipt](../../../../../re/solidworks/measurements/2026/DisclosedStockSketchRead01.json).
