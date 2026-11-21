# Feature references use creation-log times

## Expectation

A component-feature reference can reuse the document's creation date or the
referenced feature's FILETIME words.

## Actual behavior

The 2026 `moFRData_c` constructor at `sldmodu` `0x4bb34370` calls
`moLoggedNode_c::getCreationTime` at `0x4c03e070`. That getter uses the first
stamp in the node's log. Without a log or a stamp it calls `ut_getUnsetTime`.
The matching `sldutu` export at `0x3d03ebb0` returns `2592000`, not zero.
The feature's separate FILETIME fields describe another lifecycle operation.

## Workaround

Derive the reference time from the exact ordered creation log emitted for that
node. Use `logged_creation_time(timestamps=...)` with authored stamp times, or
an empty sequence for the proved absent-log sentinel. Keep the reference and
header-log state consistent. Do not populate a timestamp only in the reference.

The [model construction record](../../../../re/solidworks/records/ModelConstruction2026.md)
contains the dispatch and import evidence. Consistency of these fields still
requires native application validation of the complete generated model.
