# Temporary cylinder curve dispatch can disconnect

The SOLIDWORKS 2026 SP05.2 observer obtained a temporary modeler cylinder's
body and faces. A later out-of-process `ICurve::IsCircle` call returned
`0x80010108`. Healthy pristine controls bracketed the failed source
phase. The record confirms an interface disconnection.
[First source attempt](../../../../../../re/solidworks/measurements/2026/ImportedCylinderCurveDispatch01.json)

The topology contrast reads the cylinder's live analytic wall and planar
caps and uses the body's direct edge count. The analytic axis and radius,
mass properties and actual persistent face owner have their own checks.
