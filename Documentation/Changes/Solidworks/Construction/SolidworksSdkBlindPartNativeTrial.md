# Native lifecycle for an SDK blind-boss part

The complete SDK blind-boss candidate now passes a disclosed SOLIDWORKS
2026 SP05.2 trial on build 34.5.2.0604. The matched generated file opens
with one solid and an editable 12.75 mm depth. A 16.625 mm native edit
rebuilds and survives a clean save and fresh-process reopen.

All 25 native feature rows, the real sketch and From-plane parents,
the active configuration, and the four rectangle lines persist. The
110 numeric comparisons cover the depth, sketch endpoints, volume,
surface area and centre of mass. Both independent controls pass.

The public SDK reader recovers the original and edited driving values.
Public feature-timeline parity, held-out qualification and writer
admission remain open. The [trial record](../../../../re/solidworks/records/SdkBlindPartNative2026.md)
and [accepted narrow measurement](../../../../re/solidworks/measurements/2026/SdkBlindPartNative01.json)
bind the same SDK output to both the original and corrected observer.
