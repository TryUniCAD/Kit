# Drawing note sheet-fit comparison

The [sheet-fit observer](../../../../../../re/tooling/sw2026/drawing_notes/InspectNoteViewport01.py)
uses the exact disclosed native source and the generated drawing with the
three matched display switches. It measures the active viewport and invokes
the native sheet-fit command in a read-only document. Both input hashes stay
fixed and the observer saves no CAD file.

The leading pristine control passed. The source note opened and rebuilt
cleanly, then the second active-view query lost its COM interface. The
generated phase and trailing control could not start. The root verified the
owned process identity and closed it. The interruption establishes no
generated-candidate or sheet-fit outcome. See the
[interruption receipt](../../../../../../re/solidworks/measurements/2026/DrawingNoteSheetFitObserverFailure01.json).

The narrower retry records the initial camera, captures the native
viewport, runs `ViewZoomToSheet` and captures again. All four fresh
processes pass. The source still shows its note and the generated post-fit
image equals both empty pristine controls. The retry does not query the
numeric camera after fitting. See the
[sheet-fit receipt](../../../../../../re/solidworks/measurements/2026/DrawingNoteSheetFitNative01.json).
