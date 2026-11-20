# Observe the SOLIDWORKS through-all scope getters

The research probe reads the actual version-34 extrude definition through `IExtrudeFeatureData2`. It observes the source immediately after `FeatureCut4` with automatic selection requested, then after rebuild, SaveAs and fresh reopen. It also reads the disclosed explicit-stock generated part and two source controls. The probe freezes the exact disclosed inputs and tools before opening the native application.

All eleven observations return `FeatureScope=True` and `AutoSelect=False` across five fresh SOLIDWORKS 2026 SP05.2 processes. The native observer preserves the modeled single body, editable stock driver and ordered tree. Multibody automatic selection remains outside the measured scope.
[Procedure](../../../../../re/solidworks/records/ThroughAllAutoScopeObservation2026.md) · [Native result](../../../../../re/solidworks/measurements/2026/ThroughAllAutoScopeNative01.json)
