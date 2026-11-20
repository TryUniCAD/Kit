# Author independently shaped imported feature controls

The [topology cohort](../../../../../re/tooling/sw2026/imported_body_source/README.md#use-the-results)
uses the exact SOLIDWORKS 2026 SP05.2 modeler to author two ordinary BaseBody
sources with differently positioned cylinders. Its observer checks the
measured radius, axis, two caps, cylinder wall, body properties and actual
owning feature before save and in a fresh read-only native process.

The controlled comparison tests model geometry and archive ownership.
The [initial receipt](../../../../../re/solidworks/measurements/2026/ImportedCylinderCurveDispatch01.json)
records a disconnected temporary-edge `ICurve::IsCircle` call in the
first phase, with two healthy application controls. The revised observer
measures the wall and caps on their live surfaces and counts the body
edges directly. Native writer verification remains a separate requirement.
[Temporary curve gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/Parts/TemporaryCylinderCurveDispatchCanDisconnect.md)
