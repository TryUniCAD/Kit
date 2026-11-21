# Native through-all automatic scope query

The ordinary one-stock source calls `FeatureCut4` with both `UseFeatScope` and `UseAutoSelect` true. The 2026 SP05.2 definition immediately reports `FeatureScope=True` and `AutoSelect=False`. The same values persist through rebuild, SaveAs and fresh reopen. The explicitly scoped generated control reports the same two properties before and after rebuild. This probes the definition available through the public COM interface on the disclosed one-solid geometry. [Source author](../../tooling/sw2026/ThroughAllAuthor.py) · [Native result](../measurements/2026/ThroughAllAutoScopeNative01.json)

## Observation

The pinned installed `IExtrudeFeatureData2` metadata at library version 34.0 returns `VARIANT_BOOL` for both getters. `FeatureScope` is DISPID `34` and `AutoSelect` is DISPID `35`. The general API defines those properties separately. The actual file and runtime owners come from the exact-build research and the measured calls. [API reference](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IExtrudeFeatureData2~AutoSelect.html) · [Archive and runtime owners](ThroughAllSelectedBodyConstruction2026.md)

The [probe](../../tooling/sw2026/throughsource/ProbeThroughAutoScope01.py) uses the signed geometry predictions and exact native through-all observer from the disclosed selected-stock trial. It captures the properties on the newly authored D01 shape immediately after creation, after rebuild and immediately after SaveAs. The same file is opened read-only in another process. The tested generated selected-stock part and both disclosed source controls retain the original input hashes. Every phase verifies the installed executable SHA-256, the modeled geometry, the recursive tree, the real D1 and zero native feature errors or warnings.

| Phase | Initial | Rebuilt | After save |
| --- | --- | --- | --- |
| Earlier authored source, leading control | `true, false` | `true, false` | |
| New D01 `UseAutoSelect=True` | `true, false` | `true, false` | `true, false` |
| New D01 read-only reopen | `true, false` | `true, false` | |
| Explicitly selected generated part | `true, false` | `true, false` | |
| Earlier authored source, trailing control | `true, false` | `true, false` | |

Each pair is `FeatureScope, AutoSelect`. All eleven observations agree across five distinct native processes. Both controls pass. The disclosed freeze is SHA-256 `7f004ee4520d16d13bed5c6f76a732923b2bfb53bf63db59063b20f175c4c89f`. The canonical guest receipt is `48f6767b85bced3f5f48e01d7476c541df21e6575727ac0e5bb9bc111f99d1d2`.

The following commands created packet 01 and started its leading control. The record binds the remaining phases in order as `Author`, `Reopen`, `Selected` and `After`.

```sh
python3.14 -I -B re/tooling/sw2026/throughsource/ProbeThroughAutoScope01.py freeze

packet='\\Mac\Home\Documents\UniCAD\Oracle121Takeover\ThroughAutoScope01'
freeze_sha=7f004ee4520d16d13bed5c6f76a732923b2bfb53bf63db59063b20f175c4c89f
prlctl exec 'Windows 11' --current-user py -3.12 -B \
  "$packet\ProbeThroughAutoScope01.py" phase "$packet\Freeze.json" "$freeze_sha" Before
```

The direct property result shows that the original author call alone cannot establish continuous automatic scope. A new multibody case must change which upstream bodies intersect the cut and measure the selection and solid result after a fresh reopen. Whole-source admission, explicit dynamic neutral selections and public registration retain their existing gates. No sealed payloads were opened and this result carries zero held-out or corpus credit.
