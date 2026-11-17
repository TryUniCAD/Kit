# Bind planar mate references to child creation logs

The research endpoint builder derives the selected plane's creation time
from the first stamp in its generated child feature log. A plane without
a stamp uses the native unset time. An optional assertion at the process
boundary must agree with the derived value.

Both earlier authored placements re-encode exactly with the new reference
time and unchanged geometry, map counts and stream lengths. The guarded
process performs zero runtime file reads. It rejects an unknown datum or
a different creation-time assertion. Complete mate acceptance is still
open.

[Reference-time rule](../../../../../../re/solidworks/records/ModelConstruction2026.md#feature-reference-creation-time)
and [guarded measurement](../../../../../../re/solidworks/measurements/2026/GeneratedPlanarMateDatumLog01.json).
