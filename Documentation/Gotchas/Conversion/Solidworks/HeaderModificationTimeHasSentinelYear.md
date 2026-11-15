# Header modification time has a sentinel-year rule

The native header save does not replace every modification time with the
current clock. It tests the local-calendar year against the unset-time
sentinel's year and checks archive condition `0x80` first.

When the year matches and that condition is absent, calendar month zero selects
current wall time. Other months select the creation time, with current time
as fallback when creation time is `-1`. A value outside the sentinel year
passes through this branch unchanged.

Provide explicit creation and modification provenance. Do not emit the unset
sentinel as a supposedly stable saved modification time based only on its
constructor assignment.

The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md#header-counter-and-save-lifecycle)
records the exact save branch and binary identity. Higher-level save callers
and generated-header native acceptance remain unfinished.
