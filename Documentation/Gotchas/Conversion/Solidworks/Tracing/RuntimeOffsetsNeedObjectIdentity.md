# Bind runtime offsets to the owning type

## Expectation

Two native stores of one to offset `+0x31c` update the same application flag.

## Observed behavior

The store at `sldappu!0x457e3d86` belongs to `CAboutDlg`, identified through its vtable and RTTI.
The store at `0x45d718ca` follows `am_GetApp` and belongs to `CAmApp`.
Only the latter has the application error mapping established by the SDK path.

## Workaround

Establish each pointer's owning type before assigning meaning to a member offset.
Follow object-producing calls, vtables, RTTI, and the actual pointer register.
Treat a matching offset or stored value as a search candidate.
The [critical repair record](../../../../../re/solidworks/records/CriticalRepair2026.md) records the refuted interpretation and exact binary identity.
