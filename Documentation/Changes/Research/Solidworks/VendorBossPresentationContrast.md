# Compare native SOLIDWORKS boss presentation

The [presentation observer](../../../../re/tooling/sw2026/ObserveVendorBossPresentation.py) opens two retained parts read-only in fresh SOLIDWORKS processes. It measures annotation views, lights, display state, visibility, material and appearance before and after an in-memory rebuild. A known part brackets the pair in two separate processes. The observer records the executable identity, open status, input digests and normal process exits.

## Usage

Use a licensed SOLIDWORKS installation and an unused output directory. Supply a JSON plan with `Control`, `VendorReference` and `SavedKitEdit` entries. Each entry supplies `path`, the input `sha256`, the ordered `profile_m` points and the expected driving `depth_m`.

```powershell
python -B re/tooling/sw2026/ObserveVendorBossPresentation.py --root . measure `
  --plan $plan --output $output --executable $executable `
  --executable-sha256 $executableHash
```

The output contains the requests, process observations and a terminal `Result.json`. The terminal `passed` field covers the measured process and input checks. The retained contrast records the observed differences.

## Verification and limits

The [contrast evidence](../../../../re/solidworks/measurements/2026/VendorBossCorpus/PresentationContrast.json) binds four successful fresh processes to SOLIDWORKS 2026 SP04.1 build `34.4.1.1011`. Each process opened read-only with zero open errors or warnings, rebuilt successfully and exited normally. Both control observations agreed. Every source digest remained unchanged.

The independently authored part and the prior native-saved Kit edit had the same four-line profile, 19.87 mm driving depth and matching solid measurements. The vendor part's assigned, hidden annotation view matched the exact rotation of its decoded `*Top` record. The saved Kit part had one unassigned view and no assigned view in either observation. All four measured lights and the material and appearance observations matched. The native configuration and display-state names and construct-plane display flag differed. [SOLIDWORKS GetViewRotation](https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAnnotationView~GetViewRotation.html), [SOLIDWORKS LightSourcePropertyValues](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDoc2~LightSourcePropertyValues.html)

The reserved source stayed outside this comparison. The existing Kit derivative was inspected without a new writer run. The [annotation-view gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Presentation/RegeneratedLightsDoNotRestoreTopView.md) records the observed loss.
