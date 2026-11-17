# Observe drawing storage save entry and validity

The SOLIDWORKS 2026 observer measures the two storage boundaries inside
the document save call. After the aggregate stop, it arms the native
`saveDoc` entry at `doccplu.dll+0x1b810`. It then arms the storage validity
test at `+0x1da03` and reads the typed EAX result. It keeps one enabled
breakpoint at a time. Each nested stop must belong to the original
COM process and save thread.

Run `InspectBlankDrawingSaveAggregateSoftwareStorageMatched.py Trial.json
--packet-sha256 HASH --verify-only` in the frozen packet to check the
tool and predecessor hashes. Run it without `--verify-only` in the pinned
AMD64 oracle. The reduced native drawing must reach both storage sites,
then save and reopen cleanly, before the generated comparison. The
results distinguish an observed storage result, a completed save with
an armed site unobserved, and debugger failure.

Both traced lanes reached the storage save entry and returned EAX 1
at root validity in the original thread and a nested save frame.
The generated blank still returned error 1 with a zero-byte target.
All three reference lanes saved and reopened. Both traced debugger
detachments passed across seven distinct native processes.
[Storage observer](../../../../../re/tooling/sw2026/drawing_storage_gate/InspectBlankDrawingSaveAggregateSoftwareStorageMatched.py) · [Owned debugger](../../../../../re/tooling/sw2026/drawing_storage_gate/DrawingSaveStorageGateDbgEng.py) · [Measured document return](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveDocumentReturnNative01.json)

The [pinned gate map](../../../../../re/solidworks/records/DrawingSaveStorageGates2026.md)
records allocation before root validation and the downstream preview
and XML boundaries. The [empty-target observation](../../../../Gotchas/Conversion/Solidworks/Oracle/Drawings/EmptySaveTargetPrecedesStorageValidation.md)
preserves the distinction between a created file and a measured storage root.
[Measured storage entry and validity](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveStorageGateNative01.json)
