# Dynamic IModeler Restore can reject a native stream

On SOLIDWORKS 2026 SP05.2, the versioned out-of-process dynamic COM call
to `IModeler::Restore` returned `0x80004002` in both same-method controls.
Each control used a fresh temporary box and a nonempty IStream supplied
by `IBody2::Save`. Both pristine application controls passed.

The separate generated type-library binding with actual IUnknown returned
the same HRESULT in both controls. [Typed receipt](../../../../../../re/solidworks/measurements/2026/LocalKernelTypedRestore01.json)

Calibrate the specific stream binding with a native Save-to-Restore
round trip before evaluating generated payloads. Use a distinct measured
binding or an independently calibrated exchange import if this control
fails. The [dynamic receipt](../../../../../../re/solidworks/measurements/2026/LocalKernelDynamicRestore01.json)
records zero candidate opens.
