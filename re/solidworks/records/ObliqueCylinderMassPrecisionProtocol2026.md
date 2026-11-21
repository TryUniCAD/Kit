# Oblique-cylinder mass precision diagnostic

Task `B04-SW2026-FREECAD-CYLINDER`, owner `assembly_occurrence`, delivery PR #121. This is a disclosed, source-authoring diagnostic for the frozen F01/F02 geometry. It preserves the [directed-hinge source probes](FreecadObliqueCylinderSign2026.md), their analytic targets, their failed default comparisons and all earlier packets. It adds no writer or acceptance result. Root alone operates the native oracle.

The exit condition for this diagnostic is four independent native process records, healthy pristine brackets and complete default/document/body observations. Oblique-cylinder conversion still requires the complete source-preserving feature chain, controlled edits/persistence and independent held-out qualification. Dependencies are the unchanged flip source tools, typed extrusion-output calls, the exact registered mass API capture and the existing oracle identity/cleanup helpers.

## Exact binding and domains

The registered metadata capture has SHA-256 `ae1cb6e0fd42acc1ca2988582af2374ef9519bae3cd868f80724ad84c145b99a`. It records the actual 2026 library version `34.0`, four interfaces and zero CAD launches. The helper rejects another registered layout before opening SOLIDWORKS.

| Owner                      | Exact registered operation                                                                                                            | Diagnostic use                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `IModelDocExtension`       | `GetMassProperties2`, DISPID `286`, return `VT_VARIANT`; inputs `VT_I4 Accuracy`, output `VT_I4* Status`, input `VT_BOOL UseSelected` | Typed call with accuracy `0`, `1`, `2`, all three positional slots and `UseSelected=False`; retain the real returned status |
| `IBody2`                   | `GetMassProperties`, DISPID `76`, input `VT_R8 Density`, return `VT_VARIANT`                                                          | Actual sole body, density `1.0 kg/m³`, before and after explicit document calls                                             |
| `IMassProperty`            | Actual registered interface on a separate `CreateMassProperty` object                                                                 | Set/read `UseSystemUnits`, retain density, volume, area and centroid without replacing the original measurement             |
| `swMassPropertiesStatus_e` | `swMassPropertiesStatus_OK=0`                                                                                                         | Require an actual integer output equal to zero                                                                              |

The document method's accuracy values select existing, default and maximum evaluation respectively. They are not the separate `IMassProperty2.AccuracyLevel` enum. Its twelve values use SI and the ordinary part's default model frame. Selection is cleared and counted. [Vendor document-method contract](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.imodeldocextension~getmassproperties2.html)

The body method has no accuracy argument. Its centroid uses body creation coordinates, retained as a separate domain; these unsited ordinary part constructions predict the same frame. Its explicit density does not establish authored material density. [Vendor body-method contract](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IBody2~GetMassProperties.html)

The by-reference status is in the middle of the typed input layout. The helper supplies a numeric placeholder at that slot, then reads the actual returned `(metrics, status)` pair. `pythoncom.Missing` would terminate pywin32's positional scan before the final boolean. The placeholder is never treated as the native status. [pywin32 invocation implementation](https://github.com/mhammond/pywin32/blob/main/com/win32com/src/PyIDispatch.cpp) · [Specific invocation gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Primitives/MassStatusOutputPrecedesUseSelected.md)

## Preserved targets and process order

`ControlBefore → F01 → F02 → ControlAfter` uses four fresh applications. The pristine control must qualify the new document and body calls against its unchanged original default measurement before either disclosed oblique case may start. Root must still execute the independent after control after an interrupted phase. Summary requires all four phase receipts; an incomplete sequence does not produce a diagnostic success.

Each oblique phase uses the exact original `ObliqueFlipAuthor.build` and `snapshot`. If the original analytic comparison fails, the recorder retains that failure and its partial snapshot, then measures the same actual single body. It does not retry geometry, mutate angles or replace the default result. It records the original default, separate legacy context, body before, document accuracy 0/1/2, body after and default reread. Every successful capture preserves the full twelve-number array and all comparisons.

The original threshold remains `rel_tol=2e-7`, `abs_tol=1e-12`. The original ten-state prediction file remains SHA-256 `17dac606d4e090dd743a5b0b2607be803adab41292292dbe72fe11cb28d8c174`; only initial states are measured here. Neither a higher-accuracy match nor `diagnostic_complete=true` changes the earlier failed source result or supplies lifecycle acceptance.

## Reproduction and custody

The two independently authored helpers are [ObliqueMass.py](../../tooling/sw2026/oblique_mass/ObliqueMass.py) and [InspectObliqueMass.py](../../tooling/sw2026/oblique_mass/InspectObliqueMass.py). Preparation copies the sixteen hash-verified original tools and four original input files unchanged into an unused external packet, adds these two helpers and the registered metadata, and produces a digest-bound serial recipe.

```sh
python -B re/tooling/sw2026/oblique_mass/InspectObliqueMass.py prepare --baseline /frozen/FlipPacket --mass-metadata /declared/CaptureObliqueMassApi01.Root.stdout --output /unused/MassPacket --guest-root '\\Mac\Home\Documents\Research\MassPacket' --guest-python 'C:\verified\python.exe'
python -B /unused/MassPacket/Tools/InspectObliqueMass.py verify /unused/MassPacket/Trial.json --packet-sha256 RECEIPT_SHA256
```

Use Python 3.11 or newer for host verification. The emitted recipe pins the already verified 64-bit guest Python. Root executes its native phase commands serially in the reserved VM, preserving all transport reports and exact oracle/license identity. No document is saved or edited by this diagnostic. Every phase rechecks immutable packet inputs after measurement; native bodies exist only in the owned session.

The first packet's `Trial.json` SHA-256 is `52a51eeaa8a6e60a1da06b0870c45f574f69242391dd3719c28c44e444462d0b`; `Recipe.json` SHA-256 is `897d874b901ff49d189b50ff0b9ede1440c8ebc57cb6aab0d49a573bbefa2da1`. It binds the original flip protocol SHA-256 `0cc67981af46bcee916354bdf90b7204c9a6bf74d89fb8104636e2728c3034d8`.

Two fresh host verifies passed. Three independent modified copies, changing registered metadata, predictions or the added tool, failed before creating native progress. All sixteen original tools and all four original input files remained byte-identical. The two new Python files pass syntax/AST and comment/docstring checks; six recipe commands use canonical absolute Windows paths. These are host-only checks: zero new native launches, hidden reads or writer outputs at freeze. Native mass precision, geometry acceptance, edits, save/reopen and held-out support remain unmeasured by this packet.
