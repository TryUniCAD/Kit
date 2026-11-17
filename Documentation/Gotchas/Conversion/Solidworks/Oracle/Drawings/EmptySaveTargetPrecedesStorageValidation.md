# An empty save target can precede storage validation

The generated blank drawing's SaveAs returns error 1 after event 7 and
leaves an empty target. Its measured event aggregate is zero. The matched
native input saves through events 9 and 28 and reopens successfully.
[Measured document save return](../../../../../../re/solidworks/measurements/2026/DrawingBlankSaveDocumentReturnNative01.json)

The ordinary native storage path creates or opens the file lock bytes
before it calls the structured-storage root factory. The factory then
checks its HRESULT. Another path allocates a base storage wrapper
whose backing root can still be absent. The empty file observation
therefore leaves both storage gates open.

Measure entry to the storage save and the typed root-validity return in
the matched native lane before sampling the generated lane. If the
validity stop is unobserved, preserve that instrument result and
trace the earlier entry and factory boundaries separately.
[Native storage gate map](../../../../../../re/solidworks/records/DrawingSaveStorageGates2026.md)
