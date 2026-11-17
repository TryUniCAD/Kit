# Compare the generated and native drawing save event aggregate

The SOLIDWORKS 2026 observer puts a software execution breakpoint at the
same pinned native save event in a reduced-native drawing and the generated
blank that leaves an empty save target. It runs the two traced lanes at the
same input and output paths between two pristine native controls.

Run `InspectBlankDrawingSaveAggregateSoftwareMatched.py Trial.json
--packet-sha256 HASH --verify-only` to verify frozen inputs and observer
hashes without SOLIDWORKS. In the pinned AMD64 oracle, omit
`--verify-only` to measure the four-byte event aggregate and callback
sequence. The reduced-native control must save and reopen cleanly.
The generated branch must reproduce the existing failure footprint.
Both trace stops and detachments must be observed.

The matched native run observes zero at the aggregate test in both
traced lanes. The generated blank still returns `[false, 1, 0]) after
event 7 and leaves a zero-byte target. Both pristine brackets and the
reduced native lane save and reopen successfully. Both debuggers detach
cleanly. The generated failure occurs past the listener aggregate test.
[Matched observer](../../../../../re/tooling/sw2026/InspectBlankDrawingSaveAggregateSoftwareMatched.py) · [Native comparison](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveAggregateSoftwareMatchedNative01.json)
