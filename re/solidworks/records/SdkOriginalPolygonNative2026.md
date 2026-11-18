# Original locked polygons through the complete SDK writer

The [native source lock](../v2026/heldout/polygon/Lock.json) predates the
original polygon emitter and records three unchanged SOLIDWORKS parts.
The complete SDK writer at `189eccc0639d0435e7ecff5b866df13fc6cd1308`
is frozen before candidate generation. The
[preparer](../../tooling/sw2026/PrepareSdkPolygonCohort.py) consumes only
the locked neutral sketch and extrusion intent. It creates the ordered
line loop, its driving length and the complete file through the shared
SDK builder. It also checks the independent polygon area, perimeter and
centroid before materializing any native candidate.

For each case, two guarded builds generate identical bytes. Typed
preparation re-emits all ten streams unchanged. A separate mathematical
composer agrees on the same streams. All three candidate hashes are
fixed before the [native observer](../../tooling/sw2026/InspectSdkPolygonCohort.py)
opens the original files. The preparer and all twelve guarded workers
perform zero original native-file reads.

A disclosed triangle first passes the SDK lifecycle through four
processes and 90 numerical checks. The original cohort then opens the
unchanged native reference, the generated part, and the saved edited
part in separate processes for each of the three cases. Both pristine
controls pass. Every generated original opens with one solid before
rebuild. The original and SDK-generated trees match at 25 rows, and
each independently predicted depth edit survives clean save and reopen.

| Original source | Sketch lines | Native depth in mm | Reopened depth in mm | Numeric comparisons |
| --- | ---: | ---: | ---: | ---: |
| H3 scalene | 3 | 13 | 16.25 | 126 |
| H5 irregular | 5 | 7 | 8.75 | 182 |
| H7 irregular | 7 | 17 | 21.25 | 238 |

Geometry checks cover the actual sketch endpoints and one body's
volume, surface area and centre of mass. All native load, rebuild and
save checks pass without errors or warnings. The original source files,
generated inputs and license inventory retain their identities.

The [receipt](../measurements/2026/SdkOriginalPolygonNative01.json)
records all eleven native phases, 546 numerical comparisons, the
complete generation closure, and the independent source and output
hashes. This is held-out acceptance for the ordinary forward blind
polygon construction. Public writer invocation and production FCStd
corpus admission need separate measurements.
