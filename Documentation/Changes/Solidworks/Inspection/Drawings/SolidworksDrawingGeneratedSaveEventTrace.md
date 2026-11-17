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

Host verification passed. The matched runtime comparison remains pending.
[Matched observer](../../../../../re/tooling/sw2026/InspectBlankDrawingSaveAggregateSoftwareMatched.py) · [Reduced-native control](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveAggregateSoftwareNative01.json)
