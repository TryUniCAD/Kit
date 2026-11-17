# Observe the native drawing document save return

The SOLIDWORKS 2026 drawing observer adds a second software execution
stop at `doccplu.dll+0x16421`. It removes the successful aggregate stop
at `+0x15966`, arms the document save return stop and resumes the same
SaveAs call. The new stop verifies the original process, thread and
stack before reading the low 32 bits of RAX.

Use `InspectBlankDrawingSaveAggregateSoftwareReturnMatched.py Trial.json
--packet-sha256 HASH --verify-only` in the frozen packet to check custody
locally. Run it in the pinned AMD64 oracle without `--verify-only`. The
reduced-native lane must measure a zero event aggregate and a nonzero
document save return, then reopen successfully. The generated lane
records an observed EAX or the confirmed save return after a wait with
no document-return stop. A debugger timeout or fault has a separate
verdict. Two pristine drawings bracket the traces.

Both traced lanes reached both stops in the same frame and returned zero
at the aggregate test. EAX at the document return was 1 for the reduced
native drawing and 0 for the generated drawing. The generated drawing
still left a zero-byte target after event 7. All three native references
saved and reopened. Both debugger detachments passed across seven
distinct native processes.
[Return observer](../../../../../re/tooling/sw2026/drawing_doc_return/InspectBlankDrawingSaveAggregateSoftwareReturnMatched.py) · [Owned debugger](../../../../../re/tooling/sw2026/drawing_doc_return/DrawingSaveAggregateDbgEng.py) · [Matched return evidence](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveDocumentReturnNative01.json)
