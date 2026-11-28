# EvaluateAll does not indicate equation success

The expected shortcut is to grade `IEquationMgr.EvaluateAll` as an ordinary integer success code. The official [2026 API contract](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IEquationMgr~EvaluateAll.html) documents the same return for both outcomes. The installed 34.0 metadata confirms an I4 return, which does not change that semantic limitation.

Record the value, then verify actual equation count, row text, enabled/global ownership, dimension owner and SI value, rebuild diagnostics, independently predicted geometry, live edit and save/fresh reopen. Do not replace those checks with a truthiness test. The [source protocol](../../../../../../re/solidworks/records/NativeEquationSourceProtocol2026.md) follows this rule and retains raw equation values/statuses without guessing their unit domain. Native source measurements remain pending at its initial freeze.
