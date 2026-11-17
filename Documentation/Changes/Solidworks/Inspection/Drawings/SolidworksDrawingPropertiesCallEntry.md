# Observe entry and return of drawing document properties save

The SOLIDWORKS 2026 observer splits the remaining properties boundary
at the call instruction `doccplu.dll+0x1df56` and its return
`+0x1df5b`. It retains the measured event aggregate, original
save thread and nested-frame checks. The second stop must keep
the first stop's frame.

Run `InspectBlankDrawingSaveAggregateSoftwarePropertiesEntryMatched.py
Trial.json --packet-sha256 HASH --verify-only` to verify the
frozen predecessor, inputs and tools. Omit `--verify-only`
in the pinned AMD64 oracle. The reduced native drawing must
deliver both stops, save and reopen successfully. The generated
lane distinguishes a delivered call entry, a delivered return
and a completed save with an armed site unobserved.

The observer preserves explicit removal, restored original
instruction bytes and debugger absence as separate checks.
The source chain retains the failed preview attempt and the
qualified properties repeat. Native call-entry results are pending.
[Entry observer](../../../../../re/tooling/sw2026/drawing_properties_entry/InspectBlankDrawingSaveAggregateSoftwarePropertiesEntryMatched.py) · [Owned debugger](../../../../../re/tooling/sw2026/drawing_properties_entry/DrawingSavePropertiesEntryDbgEng.py) · [Measured post-call comparison](../../../../../re/solidworks/measurements/2026/DrawingBlankSavePropertiesGateNative01.json)
