# Compare drawing save failure with a deliberate veto

The SOLIDWORKS 2026 blank drawing observer records the visible document path, save flag and target file metadata around the existing COM save callbacks. It also observes autosave callbacks and runs a separate deliberate veto on the same reduced native input.

Three native controls saved and reopened in an eight-process run. The generated blank and deliberate veto both returned `[false,1,0]` after event 7. The generated attempt left a zero-byte target. The deliberate veto left the target absent. The exact generated return branch remains open.

Two debugger setup attempts stopped before a traced save. The passive pristine controls saved and reopened in both attempts.

[Repeat the diagnostic](../../../../../re/solidworks/records/DrawingSaveEventState2026.md) · [Native receipt](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveEventStateNative01.json) · [Debugger setup receipt](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveAggregateSetupNative01.json)
