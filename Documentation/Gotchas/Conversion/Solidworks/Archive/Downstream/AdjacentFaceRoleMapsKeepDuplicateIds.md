# Adjacent face role maps keep duplicate IDs

## Expectation

An edge reference's embedded `f10` lists distinct adjacent face IDs, so equal values can be deduplicated or its rows sorted by face number.

## Actual behavior

The exact 2026 map is signed role key → allocated face-row ID. Keys 0/1 denote the selected coedge's left/right roles. Keys 2/3 are conditional start/end face fallbacks. The setter resolves the actual face through downstream `f480` to its checked `f48` row and stores that row's ID. It does not store a face node ID or the row index.

Equal values at distinct keys are retained. A successful repeated assignment to the same key overwrites. A null face, negative role key or zero lookup result inserts nothing and does not erase an older association. Native store walks ascending signed keys. The right-face getter checks null partner but does not discard a partner face equal to the left face.

A seam reaching this ordinary role path can therefore retain the same actual face ID under both keys 0 and 1. This map-boundary fact does not qualify every seam/factory/ambiguity branch.

## Workaround

Generate actual role incidences and preserve their signed keys. Do not deduplicate by face value, sort by geometry, or force four rows when the previous/next edge-ID lookup succeeds. Keep raw wire retention and native reconstruction separate.

[Source and exact pins](../../../../../../re/solidworks/records/DownstreamFreshReferenceAssignments2026.md) bind setter `0x4b53b540`, actual-face lookup `0x4b528a90`, signed map subscript `0x4b2d29b0` and ordered store `0x4b53b0b0`. No live malformed-map or seam acceptance is claimed.
