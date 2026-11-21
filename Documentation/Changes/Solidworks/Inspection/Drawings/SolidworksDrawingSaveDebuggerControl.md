# SOLIDWORKS drawing save debugger control

The drawing save research records a third debugger control on SOLIDWORKS 2026 SP05.2. Enabling and verifying `DEBUG_ENGOPT_INITIAL_BREAK` obtained the owned initial stop. The processor breakpoint was armed. The observer received no aggregate sample before completing its wait.

The reduced native control and two pristine brackets saved and reopened without errors or warnings in six distinct processes. Explicit breakpoint removal failed. The observer detached from the owned process and verified debugger absence. The generated drawing's internal save branch remains unmeasured.

[Native control receipt](../../../../../re/solidworks/measurements/2026/DrawingBlankSaveAggregateControlNative01.json) · [Debugger setup](../../../../Gotchas/Conversion/Solidworks/Oracle/DebuggerAttachRequestNeedsAnInitialStop.md)
