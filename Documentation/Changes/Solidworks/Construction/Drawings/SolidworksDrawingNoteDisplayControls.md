# Drawing note document display controls

The internal note composer accepts an explicit `DisplayGrid` Boolean and
conveys it through the drawing's generated Definition. The grid bit is separate
from the two annotation-display bits. `ModelDefSettings.DisplayBits` already
supplies the annotation switches without carrying an opaque preference word.
The constructor keeps prior defaults for callers that omit the grid option.

The [guarded worker](../../../../../re/tooling/sw2026/drawing_notes/BuildNoteSdk01.py)
accepts `display_grid`, `display_annotations` and `display_all_annotations`
in its disclosed intent. Use the [preference probe](../../../../../re/tooling/sw2026/drawing_notes/InspectNoteGrid01.py)
and [display comparison](../../../../../re/tooling/sw2026/drawing_notes/ObserveNoteDisplayFlags01.py)
on the frozen read-only native packet with its exact build, API and input
hashes. These tools do not save the drawing or write preferences.

Eight fresh processes passed, including the two pristine controls and a native
source with rendered text. All five generated files opened and rebuilt
cleanly and reported the exact requested switches. The four grid-off
viewports were identical to the empty control, even with both annotation
switches enabled. Turning the grid on restored the grid pixels without a
note. Drawing rendering, held-out and public acceptance remain open.
See the [typed ownership record](../../../../../re/solidworks/records/DrawingDocumentDisplayFlags2026.md)
and [native receipt](../../../../../re/solidworks/measurements/2026/DrawingPlainNoteDisplayFlags01.json).
