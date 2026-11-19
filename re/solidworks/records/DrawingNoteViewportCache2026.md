# Native note viewport storage omission

Task `B04-SW2026-DRAWING-NOTES-C10`, owner `/root`, delivery PR #121. This research diagnostic isolates the viewport storage roles following the [generated note rebuild observation](DrawingPlainNoteMemoryChanges2026.md). The exit for this experiment is a comparison against two pristine and two annotated native controls. Populated drawing admission and held-out qualification have separate requirements.

The [preparer](../../tooling/sw2026/drawing_notes/PrepareNoteViewportCache01.py) verifies the exact previously disclosed native source, pristine control, note intent and observer closure. It stages five private copies of the native source using the existing container emitter and the source's actual stream identities. The [observer](../../tooling/sw2026/drawing_notes/InspectNoteViewportCache01.py) opens each copy read-only with a new pinned SOLIDWORKS process, checks the real sheet/annotation tree, errors, preferences and viewport pose, and captures the viewport before rebuild, after rebuild and after the sheet-fit command. It saves no CAD files and changes no preferences.

| Diagnostic role | Omission | Retained logical streams |
| --- | --- | ---: |
| Full repack | | 29 |
| Display lists | `Contents/DisplayLists` | 28 |
| View-bucket lists | `Contents/VBLists` | 28 |
| Display update stamp | `_DL_VERSION_19000/DLUpdateStamp` | 28 |
| Combined | All three above | 26 |

The retained stream bytes, identities, type IDs and relative order match the original for each copy. All copies and controls stay private research artifacts. Five host process checks passed, including three expected refusals. The exact job SHA-256 is `507c1f99a6a8125e0cf9154a6114eb5f5b44a78abe394d512dcd2d68e8c6d527` and the recipe SHA-256 is `0a087457d5d961ae75b0a7f1de0aaf8d94805a6d53465ab8e8c45f185f8c29a2`. The [change entry](../../../Documentation/Changes/Solidworks/Inspection/Drawings/Notes/DrawingNoteViewportStorageOmission.md) describes invocation and boundaries.

## Native result

All nine processes opened with zero errors or warnings and measured zero features with native errors or warnings. Both pristine and both unchanged annotated controls agree at every capture point. The full repack and all four omission copies preserve the annotated source's exact bitmap at initial open, after rebuild and after sheet fit. Actual note extent and text positions, ordered tree, display preferences and viewport pose also match. The tested note renders through rebuild with all three streams absent.

The [numeric receipt](../measurements/2026/DrawingNoteViewportCache01.json) links the exact guest observations to the 29/28/28/28/26 stream variants. Raw result SHA-256 `d7c37d23a656c4df88bfe48446aee578d98c208f95d06fc01d035d010879e588`. Generated drawing acceptance remains open.

The follow-up `--profile seven` keeps the seven stream roles emitted by the generated drawing and removes every other stream from the same native source. It requires the complete graphics-omission result with `--cache-basis PATH` and produces a new, separately hash-locked six-process packet.
The validated seven-role packet has trial SHA-256 `bb81d7cc7dc46352aed134e6a57cf3530f5e4f229a9068b6ce32fa43a621cd11` and recipe SHA-256 `a9c21e7c43da7a95f4db5700bf353c7d1928c0e3b18708f7bd9e36b9061b461f`. Host verification, a wrong-hash refusal and a native-mode-on-host refusal passed before any native launch. The earlier preparation with a stale observer argument table remains unexecuted.
