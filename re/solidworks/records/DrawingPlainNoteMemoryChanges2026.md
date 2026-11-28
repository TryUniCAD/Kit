# Generated drawing note pixels disappear on rebuild

Task `B04-SW2026-DRAWING-NOTES-C10`, root-owned SOLIDWORKS 2026 SP05.2 oracle, delivery PR #121. The test opens the [original display-matrix inputs](../measurements/2026/DrawingPlainNoteDisplayFlags01.json) read-only. It uses pristine blank drawings before and after and an unchanged native drawing with the disclosed note. The generated drawing is the exact grid-off file with both annotation settings enabled.

The [frozen observer](../../tooling/sw2026/drawing_notes/ObserveNoteMemoryChanges01.py) captures the initial frame after rebuild, replaces only the existing note text, clears selection, redraws and captures before and after a subsequent rebuild. It then inserts a second unattached native note at a distinct sheet location and repeats the same capture and rebuild. Both pristine controls run the insertion only. The observer checks actual sheet note positions, names, text and count through rebuild and verifies unchanged display preferences and input hashes. It saves no drawing and changes no preferences.

| Drawing | Changed pixels after text redraw | After text rebuild | After insertion redraw | After insertion rebuild |
| --- | ---: | ---: | ---: | ---: |
| Pristine before | | | 847 | 847 |
| Disclosed native note source | 239 | 239 | 847 | 847 |
| Generated note drawing | 842 | 0 | 847 | 0 |
| Pristine after | | | 847 | 847 |

All four processes opened with zero errors or warnings. The initial generated frame matches the pristine initial frame. Both edited and inserted notes remain in the generated sheet annotation list after rebuilding. A directly native-authored second note therefore has the same presentation failure in this document. The observations locate when the visible changes disappear. The underlying rendering owner, durable editing and held-out qualification remain open.

The [RGB comparison tool](../../tooling/sw2026/drawing_notes/SummarizeNoteMemoryChanges01.py) validates the raw BMP and pixel hashes, compares RGB values and emits [the numeric receipt](../measurements/2026/DrawingPlainNoteMemoryChanges01.json). Raw oracle receipt SHA-256 `9857530b8c2eccb14f567a107381edd6556736bef7812b11be22f3f69922d5f1`, trial `70570ac768359726b03febb6b34d1738472e6368d29800039090dc62494e4c18`. Guest build `34.5.2.0604`. The two locked original drawings remain sealed.

[Change entry](../../../Documentation/Changes/Solidworks/Inspection/Drawings/Notes/DrawingNoteMemoryChanges.md) · [Gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Drawings/NoteRedrawCanDisappearOnRebuild.md)
