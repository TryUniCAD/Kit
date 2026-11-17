# Observe the drawing preview and third-party save gates

The SOLIDWORKS 2026 observer continues the qualified storage trace with
the two preview-only getter results at `doccplu.dll+0x1dd1b` and
`+0x1dd2b`. When both results are zero it arms the ordinary third-party
save call at `+0x1dfb5`. It checks the original process and save thread,
a nested frame at the first getter, and that same frame at later stops.

Run `InspectBlankDrawingSaveAggregateSoftwarePreviewMatched.py Trial.json
--packet-sha256 HASH --verify-only` against the frozen packet to check
its exact storage predecessor and script hashes. In the pinned AMD64
oracle, omit `--verify-only`. The reduced native lane must reach the
three stops, save, reopen and detach cleanly before tracing the
generated input. The observer records typed getter results and
separates a completed save with an armed stop unobserved from a
debugger failure. Both pristine native brackets must pass.

The frozen host custody check passed. The native comparison is pending.
[Preview observer](../../../../../re/tooling/sw2026/drawing_preview_gate/InspectBlankDrawingSaveAggregateSoftwarePreviewMatched.py) · [Owned debugger](../../../../../re/tooling/sw2026/drawing_preview_gate/DrawingSavePreviewGateDbgEng.py) · [Qualified storage route](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveStorageGateNative01.json)
