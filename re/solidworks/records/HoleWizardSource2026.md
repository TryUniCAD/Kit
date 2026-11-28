# SOLIDWORKS 2026 Hole Wizard source acquisition

`B04-SW2026` in PR #121 owns this disclosed source acquisition. The [author](../../tooling/sw2026/hole_source/AuthorHoleWizard.py) creates two independent source designs through the native Hole Wizard. The [host receipt](../measurements/2026/HoleWizardInstalledApi01.json) binds the exact installation metadata, source predictions, packet closure and host refusals. No native source, writer, held-out or corpus conversion qualification has been recorded.

## Installed interface

The Windows metadata collector read the registered `34.0` application and constants type libraries. It pinned `sldworks.exe` `34.5.2.0604`, executable SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe` and ProgID `SldWorks.Application.34`. The captured metadata is 128,257 bytes, SHA-256 `2819a07ed9096886bb54d8e6244b4da12d4a3560faf855292a300b447fd38784`. [ReadHoleApi.py](../../tooling/sw2026/hole_source/ReadHoleApi.py) retains the capture method with exclusive output. The full capture stays outside Kit. It contains API declarations and enum values. The capture requires no SOLIDWORKS process.

The installed `IFeatureManager.HoleWizard5` member has DISPID `222` and 27 ordered inputs. `Length` is the eighth input and is slot-specific. The case plans pass `-1` there and for unused optional dimensions. Counterbore `Value1` and `Value2` are the upper diameter and depth, with `Value3 = 0` for the head-clearance override. Numeric geometry uses metres. [HoleWizard5 argument contract](https://help.solidworks.com/2021/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IFeatureManager~HoleWizard5.html)

`IWizardHoleFeatureData2` has distinct get and put invocations for `HoleDiameter` at DISPID `11` and `CounterBoreDepth` at `20`. The packet observes the installed type, active end, retained catalog identity, actual position sketch and native display dimensions before and after the separate edit. It binds actual geometry to the one owned solid and checks analytic volume, area and centre of mass. [HoleDiameter](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IWizardHoleFeatureData2~HoleDiameter.html), [valid properties by hole type](https://help.solidworks.com/2023/english/api/sldworksapi/table_of_wizard_hole_types_and_valid_properties.htm), [selection access protocol](https://help.solidworks.com/2022/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IWizardHoleFeatureData2~ReleaseSelectionAccess.html)

## Cases

| Case | Catalog and proposed native subtype | Independent native edit |
| --- | --- | --- |
| `PlainThrough` | ANSI Inch All Drill Sizes `#97`, `swHoleThru = 25` | Hole diameter 6.37 mm to 8.11 mm |
| `CounterboreThrough` | ISO Hex Cap Screw `M6`, `swCounterBoreThru = 14` | Counterbore depth 3.73 mm to 5.19 mm |

Each stock is a fresh rectangular sketch and blind boss. Each source uses a different off-centre location on the actual top planar face and a forward through-all hole. The public examples establish the case-sensitive catalog pairings and face-selection mark. The independent [case model](../../tooling/sw2026/hole_source/HoleWizardPlan.py) computes the geometry and edit predictions from disclosed neutral dimensions. [ANSI example](https://help.solidworks.com/2024/English/api/sldworksapi/Insert_Hole_Wizard_Slot_and_Hole_Example_VB.htm), [ISO example](https://help.solidworks.com/2025/english/api/sldworksapi/Create_Holes_using_Hole_Wizard_and_Sketch_Points_Example_VB.htm), [2026 Hole Wizard custom size](https://help.solidworks.com/2026/English/SolidWorks/sldworks/r_HIDD_DVE_HW_HOLE_SPEC.htm)

## Reproduction

Freeze and verify with an unused packet directory outside Kit and the pinned installed capture.

```sh
python3.14 -I -B re/tooling/sw2026/hole_source/HoleWizardPacket.py prepare \
  /absolute/path/HoleWizardSourcePacket02 \
  --installed-api /absolute/path/InstalledHoleApi.json \
  --guest-root 'C:\KitHoleWizardSource02'
python3.14 -I -B /absolute/path/HoleWizardSourcePacket02/Tools/HoleWizardPacket.py verify \
  /absolute/path/HoleWizardSourcePacket02/Packet.json \
  69f86ffe019d2629b36b4fd83aff9c6e46ce5e935fefc2e532bbce3dc5ed80e2
```

The frozen manifest pins the 14 Python scripts, exact installed capture, unchanged L1 boss control and source plan. The plan SHA-256 is `df9141af8b8d79217bf217904fc55251b7f0ad96f1d8279a5e7e9413f5213d58`. The checked host packet resolved successfully in a fresh process. Independent scratch copies refused an incorrect packet hash, changed metadata with and without rebinding the manifest, a rehashed changed prediction, an extra file and a same-byte symlink. Guest-only commands refused on the host. All 14 scripts parsed with Python 3.12 grammar.

Use the frozen script with current-user Windows Python 3.12 `-E -B`. Pass `run <absolute Packet.json> <packet SHA-256> <phase>` once per phase in order. The oracle owner completed `Metadata` on the exact packet. The installed capture matched byte for byte and the registered through-all enum was `1`, with zero SOLIDWORKS process starts. The current packet has the [guest enum binding receipt](../measurements/2026/HoleWizardEqualityBinding01.json).

The six native phases are `Before`, `AuthorPlainThrough`, `ReopenPlainThrough`, `AuthorCounterboreThrough`, `ReopenCounterboreThrough` and `After`. The separate native reopens are read-only and verify original and edited file hashes before and after observation. The before and after controls must be healthy and unchanged.

Native and exchange saves, detailed COM observations and any unqualified early checkpoint remain in the owned guest-local directory. After all phases pass, `summary <absolute Packet.json> <packet SHA-256> <unused guest result path>` verifies their shared custody, independent native lifetimes and source evidence. The summary contains only hashes, counts and verdicts.

The exit for this acquisition is two exact native-written sources with verified original and edited geometry, immutable reopen and healthy controls. Physical archive ownership, a shared model-only writer and any held-out confidence remain separate open work.

## Bound stock-face identity

The source author initializes the selected-body identity comparison from the registered release-34 object-equality enum.
The earlier author relied on an enum member that its base class did not initialize.
This was found by inspecting the source before either native authoring phase.
The new packet retains the same author intents, metadata input hash and immutable control.
It uses SHA-256 `69f86ffe019d2629b36b4fd83aff9c6e46ce5e935fefc2e532bbce3dc5ed80e2`.
Prepare it under a fresh directory using `C:\KitHoleWizardSource02` as its guest root.

The new guest Metadata phase passed.
The original registered through-all condition and the selected-body equality enumerator both resolve to `1` on build `34.5.2.0604`.
The first packet's observation remains historical evidence.
The current packet starts its next measurement at `Before`.
[Guest binding receipt](../measurements/2026/HoleWizardEqualityBinding01.json)
