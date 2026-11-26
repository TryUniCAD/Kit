# Length unit and display precision are separate

`IModelDoc2.GetUnits()` returned `[0, 1, 1, 4, 0]` for the two generated exact-SI sketch candidates and `[0, 1, 8, 2, 0]` for their native references. The first entry in both sets denotes millimetres. The records also differ in the fraction-value and significant-digit positions. Fraction formatting is only active for the documented inch modes. [SOLIDWORKS API field reference](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDoc2~GetUnits.html)

When qualifying display settings, compare the complete measured unit record and the applicable formatting fields alongside the length unit. Keep exact SI coordinate fidelity and display formatting as separate acceptance checks. [Exact-sketch native evidence](../../../../../../re/solidworks/records/VendorBlindBossNativeSketchProof.json)
