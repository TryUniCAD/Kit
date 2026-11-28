# A drawing veto and a failed save can share the same status

SOLIDWORKS `34.5.2.0604` returned `[false,1,0]` and emitted only `FileSaveAsNotify` for both the generated blank and a deliberate event 7 veto on the reduced native blank. The target was absent during that event in both lanes. After the call, the generated attempt left a zero-byte file and the deliberate veto left the target absent. [Matched native comparison](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveEventStateNative01.json)

Compare target existence and extent after return when a veto and a save failure have the same status and callbacks. Use the listener aggregate or a downstream trace to identify the generated save's internal branch. [Observation protocol](../../../../../re/solidworks/records/DrawingSaveEventState2026.md) · [Native branch map](../../../../../re/solidworks/records/DrawingSavePostEventBranches2026.md)
