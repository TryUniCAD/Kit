# Bind required extrusion output arguments in the native source observer

PR #121 adds explicit registered `InvokeTypes` calls for the oblique-cylinder direction and selected-end getters. The original dynamic zero-argument getter omitted four required output pointers and failed with `DISP_E_PARAMNOTOPTIONAL`. The source workflow also creates each disclosed raw-record directory before constructing its recorder.

The [failure/retry record](../../../../../re/solidworks/records/FreecadObliqueCylinderObserverRetry2026.md) preserves both passing controls, actual pre-failure angular/axis/driver measurements and the original direction-prediction mismatch. Its [receipt](../../../../../re/solidworks/measurements/2026/FreecadObliqueCylinderObserverRetry01.json) records the metadata-derived calling plans and host process checks. The [specific gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/Primitives/ObliqueExtrusionOutputsRequireTypedInvoke.md) distinguishes a dynamic COM receiver from inspected generated-class defaults.

The separately frozen observer retry preserves the original neutral cases, predictions and control bytes. Native body, edit/save/reopen and source-lock acceptance remain pending. This changes research tooling only; it adds no writer, hidden-input access or production support.
