# Trace the drawing save event aggregate with a software breakpoint

The SOLIDWORKS 2026 drawing research observer adds a software execution
breakpoint at the pinned event aggregate check in `doccplu.dll`. The
controlled test uses an ordinary reduced-native drawing between two
pristine brackets on build `34.5.2.0604`. The pin includes the exact module
hash and the owned COM process identity. The observer distinguishes
the save call result from the debugger wait and verifies detachment.

Run `InspectBlankDrawingSaveAggregateSoftwareControl.py Trial.json
--packet-sha256 HASH --verify-only` with the frozen deck to verify its
inputs without SOLIDWORKS. In the pinned AMD64 oracle, omit
`--verify-only` to run the native control. The initial debugger stop,
aggregate sample, save and fresh reopen each have separate checks.
The reduced-native control reached the breakpoint after event 7. Its
four-byte aggregate was zero. The reduced drawing and the two pristine
brackets saved and reopened cleanly in six distinct processes. The
observer removed the breakpoint and confirmed debugger absence after
detach. [Native control receipt](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveAggregateSoftwareNative01.json)

[Observer](../../../../../re/tooling/sw2026/InspectBlankDrawingSaveAggregateSoftwareControl.py) · [Debugger implementation](../../../../../re/tooling/sw2026/DrawingSaveAggregateDbgEng.py) · [Pinned save branch](../../../../../re/solidworks/records/DrawingSavePostEventBranches2026.md)
