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
