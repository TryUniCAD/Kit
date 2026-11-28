# Populated sheet-metal native capture request

Use the dedicated SOLIDWORKS oracle owner and a fresh private output directory. Bind the actual executable build, executable digest, and `sldsmmu.dll` and `sldmodu.dll` digests. Compare the installed SP04.1 build `34.4.1.1011` with its [static findings](SheetMetalPerBodyStatic2026.md). Treat any other build as a separate cohort. Run a healthy stock control in a fresh process before and after the batch.

Author fully constrained XY rectangles with the listed world offsets, positive local thickness, and explicit bend settings. Use disjoint, unmerged solid bodies. The supplied dimensions are millimetres. Record the actual SI API arguments and readbacks.

| Save                         | Authoring contrast                                                                                                                                                                                                                                                                        |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `A-only` and `A-only-repeat` | Independently author base flange A from `(0,0)` to `(41,23)`, thickness `1.25`, inside bend radius `1.75`. Save each in its own owned session.                                                                                                                                            |
| `A-then-B`                   | Keep A, then add B from `(67,11)` to `(96,28)`, thickness `1.25`, radius `1.75`, with solid merge disabled.                                                                                                                                                                               |
| `B-then-A`                   | Author the same two unmerged bodies in reverse order. Record the actual body, feature and cut-list order.                                                                                                                                                                                 |
| `A-edge`                     | A plus a blind flange on the upper-face long edge at `y=23`. Select by endpoints and body identity. Use `90°`, length `13`, inside radius `1.75`, bend outside, inner virtual sharp, zero offset, and no relief.                                                                          |
| `held-out`                   | Independently author B′ then A′. A′ spans `(−14,7)` to `(23,33)`, and B′ spans `(49,−19)` to `(71,−4)`. Use thickness `1.6`, radius `2.3`, and a `75°` blind flange on A′’s upper-face short edge at `x=23`, length `17.5`. Seal the original archive and receipt before deriving a rule. |

Keep the six native `.SLDPRT` saves and per-file hash-bound observations. Record the active configuration, `SaveAs` outputs, exact body count and order, per-body bounds and mass/center, feature names and types, persistent identities, parent relationships, cut-list membership, folded and flat state, and the selected edge witness with its actual body and topology owner. A geometry match does not substitute for persistent selection identity. Preserve load, rebuild and native feature diagnostics. For `A-edge` independently edit flange length from `13` to `16.25`, rebuild, measure, save the edit, restore `13`, rebuild, save the restoration and verify both saves in fresh processes. Keep the phase identities, control observations, and archive hashes. Preserve the original failures and the original files.

The existing `RunSolidWorksScope.ps1` harness has dedicated host ownership and private output guards but needs a sheet-metal authoring binding. Use the installed exact-build COM API and bind the actual arguments and precision. [Base flange authoring](https://help.solidworks.com/2023/english/api/sldworksapi/Insert_Sheet_Metal_Base_Flange_Example_CSharp.htm) · [Edge flange authoring](https://help.solidworks.com/2026/english/api/sldworksapi/Insert_Sheet_Metal_Edge_Flange_Example_VB.htm)

Run the following from the #225 checkout on each non-holdout archive using its independently obtained SHA-256. `REFERENCE_REPOSITORY` must contain Git object `b87f3b12b72874f4289b627d56e3740da2ab725b`. Use new result files. The probe uses only the tracked source of the referenced revision.

```sh
python3.14 -I -B re/tooling/sw2026/sheetmetal/InspectSheetMetalConfig.py \
  --reference REFERENCE_REPOSITORY --part PRIVATE_FILE --sha256 RECEIPT_FILE_SHA256 \
  > PRIVATE_RESULT_JSON
```

Compare the direct master's `n370/f358` membership and inherited links independently of the later-model `n16f8/f16e8` array. Compare incoming and allocated map slots to each reported target. Use the native API evidence to explain the base, body, sheet-metal and flat-pattern links and the topology reference. Refusals identify unresolved grammar; they are not decoded membership. Freeze the proposed change before using the held-out save. Byte-identical Config replay is offline segmentation evidence only.
