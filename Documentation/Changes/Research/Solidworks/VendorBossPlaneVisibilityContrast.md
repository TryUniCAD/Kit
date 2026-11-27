# Measure document-wide construct-plane visibility in SOLIDWORKS

The [source observer](../../../../re/tooling/sw2026/ObserveVendorBossPlaneVisibility.py) measures one document-wide plane display toggle in a private copy of a known vendor-authored boss. It saves the warmed copy twice at the same path and title. It then changes `swDisplayPlanes` through the document extension and saves a third snapshot. Fresh read-only processes reopen and rebuild the unchanged and toggled snapshots between two observations of the stock control.

The observer reads both the document preference and current construct-plane visibility. It compares geometry, driving dimension, per-feature visibility, display-state membership, annotation views, lights and material/appearance across the unchanged and toggled snapshots. It also compares clear stream data before and after the two no-op saves and across the toggle. This provides a baseline for save noise. [SOLIDWORKS document preference setter](https://help.solidworks.com/2023/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.imodeldocextension~setuserpreferencetoggle.html?format=P&value=), [SOLIDWORKS plane visibility getter](https://help.solidworks.com/2019/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDoc2~GetVisibilityOfConstructPlanes.html)

## Usage

Use the registered licensed executable and an unused output directory. Supply a JSON plan with `oracle_build`, `Control` and `AuthorSeed`. Each input supplies `path`, `sha256`, the ordered `profile_m` points, `depth_m`, and the expected `initial_visibility` boolean. Use independently authored inputs for the stock control and the author seed.

```powershell
python -B re/tooling/sw2026/ObserveVendorBossPlaneVisibility.py --root . measure `
  --plan $plan --output $output --executable $executable `
  --executable-sha256 $executableHash
```

The tool retains private save snapshots, request and result records, and a terminal `Result.json` in the output directory. The [compact evidence](../../../../re/solidworks/measurements/2026/VendorBossCorpus/PlaneVisibilityContrast.json) binds the measured inputs and native process results. The experiment covers document state on one vendor-authored source.

## Verification

SOLIDWORKS 2026 SP04.1 `34.4.1.1011` reported `True` on both document getters for the no-op snapshot and `False` on both getters for the toggled snapshot. The difference survived fresh read-only open and rebuild. The 19.87 mm driver, feature visibility, sole display-state name, annotations, lights and materials agreed. The part retained one solid and a volume of 10,531.1 mm³. Both controls passed and all seven task-owned processes exited normally.

The two same-process no-op captures differed in four clear streams. The toggle capture differed from the retained no-op in 21 clear streams and was saved in a later process at the same encoded path. `ThirdPtyStore/VisualStates` was byte-identical across all three captures. The stream comparison retains the save and process effects alongside the setting change for the later field-level analysis.

For the retained stopped warm-up, `--preflight` and `--preflight-sha256` identify the existing result and its digest. The continuation verifies the saves, exact working copy, inputs and controls before applying the toggle. This reuses the same working path and title. The original stop remains visible in the evidence. [Native mass readback gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Presentation/NoOpSaveCanShiftMassReadbackOneUlp.md)

The setter returned `True` while both getters reported `False`. The observer retains all three values. [Setter return gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Presentation/PlaneToggleReturnCanDifferFromDocumentState.md)
