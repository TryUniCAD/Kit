# A visible drawing note can be missing from the viewport

On SOLIDWORKS 2026 SP05.2 the disclosed generated note matched its original
source in both name and position APIs, exact text, free attachment,
individual visibility state and the complete ordered feature tree. Its
display-data API returned a valid text run and the extent API returned a
nonempty box. A native viewport capture nevertheless showed a dashed grid
with no legible note. The matching source displayed its note and both
pristine controls produced identical bitmaps.

Measure the actual rendered viewport in addition to annotation APIs when
qualifying document presentation. This case retains the exact inputs,
geometry differences and bitmap hashes in the [native receipt](../../../../../../re/solidworks/measurements/2026/PlainDrawingNotePresentation01.json).
