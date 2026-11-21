# Debugger cleanup can lose the selected process context

The paired preview-gate trial failed its explicit breakpoint-removal
check after the generated drawing's SaveAs returned. Cleanup reported
`cleanup stop OS process id returned HRESULT 0x8000ffff`. The debugger
then detached and the owned process reported debugger absence. The
full comparison retains exit 3. [Native attempt](../../../../../../re/solidworks/measurements/2026/DrawingBlankSavePreviewGateNative01.json)

Before cleanup, both traced drawings delivered zero-valued preview
getter stops in the original save thread and the expected nested
frame. The generated save returned after a debugger wait with the
next call site armed and no delivered stop. This outcome needs a
qualified cleanup repeat.

Retain the original failure and each directly observed stop. A
follow-up can reselect and verify the captured owned engine process
before removal, or verify restored original instruction bytes after
the debugger detaches. Track explicit removal, restoration and
debugger absence as separate observations.

The next properties-gate trial successfully reselected the owned
engine process. Both lanes completed explicit removal and byte
restoration checks before confirmed debugger absence. The preview
trial retains its original failed verdict.
[Qualified cleanup repeat](../../../../../../re/solidworks/measurements/2026/DrawingBlankSavePropertiesGateNative01.json)
