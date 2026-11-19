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

The [observer](../../../../../../re/tooling/sw2026/drawing_notes/ObservePlainNotePresentation01.py)
takes `verify` or `run`, a packet `--job` and its `--sha256`. Use the
reserved oracle for `run` and a fresh packet output directory. The job pins
the four file hashes, exact eight-script closure, source SDK revision and
guarded generation receipt. The first run establishes no note presentation or
public output qualification.
