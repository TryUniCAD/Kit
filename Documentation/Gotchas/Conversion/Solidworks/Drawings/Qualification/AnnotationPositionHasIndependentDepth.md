# Annotation position has independent depth

An observer may expect the Z at `IAnnotation.GetPosition` to be the actual stored sketch dimension text Z. In the two controlled SOLIDWORKS 2026 SP05.2 lifecycles, every API annotation reports `0.0001 m` while the corresponding saved text points retain both the positive and negative authored depths through edit, save and fresh reopen.

Read the embedded `moDimText_c.f38` point under the actual `moDisplayDistanceDim_c.f6a0` owner for stored placement. Retain the API position as its own observation. Compare both through the actual value and display IDs. [Native and typed measurements](../../../../../../re/solidworks/measurements/2026/DrawingSpatialTextNative01.json)
