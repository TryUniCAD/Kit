# A repeated drawing active-view probe can lose COM

The first SOLIDWORKS 2026 SP05.2 sheet-fit observer successfully queried the
native note source's initial active view. The second query failed after
rebuild and annotation inspection even though the leading control passed.
The owned read-only process also lost its COM exit methods. The exact
trigger within this sequence remains unverified.

Keep the trial uninterpreted and match a simpler sheet-fit and viewport
sequence against the same controls. Verify the owned process's creation
identity and executable digest before clearing a failed read-only session.

[Native receipt](../../../../../../re/solidworks/measurements/2026/DrawingNoteSheetFitObserverFailure01.json)
