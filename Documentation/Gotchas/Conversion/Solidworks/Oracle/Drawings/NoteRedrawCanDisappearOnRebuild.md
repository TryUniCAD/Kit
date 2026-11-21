# Note redraw can disappear on rebuild

A drawing note can visibly change immediately after a native text edit or insertion, then disappear after rebuilding the drawing. The SOLIDWORKS 2026 SP05.2 generated case retains both notes with correct text and positions in the sheet annotation list. Both pristine controls and the disclosed native note source keep the changed pixels after rebuild.

For drawing presentation checks, clear selection and capture after rebuild as well as after redraw. Compare the viewport and the model annotation inventory against independent native controls.

[Controlled observation](../../../../../../re/solidworks/records/DrawingPlainNoteMemoryChanges2026.md)
