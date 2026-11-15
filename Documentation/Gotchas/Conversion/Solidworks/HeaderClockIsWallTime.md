# The header clock returns wall time

The vendor's `su_CTime::GetTickCount` name resembles the Windows uptime API.
Using uptime milliseconds for header timestamps would follow the wrong unit
and clock domain.

The exact 2026 implementation in `swccu.dll` calls `_time64(NULL)` and returns
that value in its time object. Header update stamps use wall time in seconds.

Keep the counter and timestamp separate. Derive emitted time fields from
explicit authored wall-clock metadata, and do not interpret the vendor method
name as a millisecond counter.

The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md#header-counter-and-save-lifecycle)
records the binary hash, address and REA evidence. This static rule does not
establish acceptance of a generated header.
