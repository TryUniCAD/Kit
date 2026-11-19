# Disclosed drawing note presentation observer

The observer opens a pristine drawing before and after a matched native-source
and generated SDK note pair. It measures ordered native feature names and
types, individual visibility, text, both placement APIs, visible-document
extents, display text geometry and the viewport bitmap. Its hash-bound job
opens all inputs read-only in fresh SOLIDWORKS processes.

The first exact 2026 SP05.2 run opened both controls with zero load errors and
warnings. The in-document dependency call threw on both controls before
rebuild. The two note phases were skipped. One verified owned read-only control
needed separate cleanup after its COM exit methods became unavailable.
The source hashes stayed fixed. See the [interruption receipt](../../../../../../re/solidworks/measurements/2026/PlainDrawingNotePresentationObserverFailure01.json)
and [dependency call gotcha](../../../../../Gotchas/Conversion/Solidworks/Oracle/Drawings/DrawingExtensionDependencyCallCanThrow.md).

The second run used the application file dependency query with the same
controls and candidate bytes. All four fresh opens and rebuilds passed, and
the control bitmaps were identical. The note names, content and placement
matched through both APIs. So did all ten ordered tree rows and the sheet
properties. The source visibly showed the note. The generated viewport showed
a dashed grid and no legible note. The two bitmaps differed at 77,785 pixels,
and their measured note text heights were 3.175 mm and 3.5 mm. See the
[disclosed presentation receipt](../../../../../../re/solidworks/measurements/2026/PlainDrawingNotePresentation01.json)
and [file dependency API](https://help.solidworks.com/2023/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~GetDocumentDependencies2.html).

The [observer](../../../../../../re/tooling/sw2026/drawing_notes/ObservePlainNotePresentation01.py)
takes `verify` or `run`, a packet `--job` and its `--sha256`. Run it in
the reserved oracle with an unused output directory. The job pins the four
input files, eight-script closure and guarded generation receipt. This
evidence keeps the rendering and public output gates open.
