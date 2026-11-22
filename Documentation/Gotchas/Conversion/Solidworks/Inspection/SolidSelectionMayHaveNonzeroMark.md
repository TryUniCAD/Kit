# An exact selected solid may have a nonzero mark

After `IBody2.Select2` succeeded in the SOLIDWORKS 2026 SP05.2 ellipse source probe, `GetSelectedObjectCount2(-1)` returned one and `GetSelectedObjectCount2(0)` returned zero. The original observer reused its feature-selection mark check and stopped before measuring the selected body.

For body mass measurement, retrieve the sole object across all marks. Check its solid type and object identity against the physical body that owns the measured faces. Verify the separate mass property's selected item against the same body. [Selection count mark semantics](https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISelectionMgr~GetSelectedObjectCount2.html) · [Ellipse source record](../../../../../re/solidworks/records/EllipseBlindBossSource2026.md)
