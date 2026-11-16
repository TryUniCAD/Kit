# Loading a line catalog replaces its initialized rows

Initializing native line styles before reading a zero-row saved catalog does not, by itself, preserve those initialized rows.

The pinned 2026 `apLineStyleMgr_c::Load` first reads the signed row count, calls `deleteAll` on its current list, then appends the declared object rows in their wire order. A zero count therefore produces an empty manager at this load-return boundary. Any later repopulation is a separate lifecycle rule that requires evidence.

The independent definition builder currently emits zero catalog rows. That value cannot establish that display index zero refers to a particular authored line-style name or builtin library entry. To support an authored style, construct an explicit catalog with proven pattern semantics and consistent indices, or retain fail-closed admission until the missing mapping is established. Do not copy installed line libraries, saved rows or observed indices into defaults.

Evidence: original MFC body `[0x3c848b70,0x3c848bed)` and the exact module/function fingerprints in the [style evidence](../../../../../re/solidworks/records/RadialStyleConstruction2026.json). This is a static loader conclusion, not an observed visual defect, warning, rebuild failure or native acceptance result.
