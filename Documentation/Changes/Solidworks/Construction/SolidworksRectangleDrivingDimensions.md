# SDK rectangle driving dimensions

The internal `MakeRectDimPart` entry constructs a complete SOLIDWORKS 2026
rectangle with editable sketch width and height, followed by the existing
forward blind boss. The neutral document must explicitly own four axis
relations, two endpoint-distance relations, sketch D1/D2 and boss D1.
Finite text positions, routing, style and provenance remain explicit inputs.

The SDK creates actual point-distance values, named parameters, indexed sketch
handles and distance displays. It derives IDs, constraint-reference counts,
annotation IDs and keyword lengths from the graph. All ten streams and the
container use the existing typed SDK codecs in memory. No saved native input,
recorded field program, research import or CAD application is used by synthesis.

The existing plain rectangle and closed-polygon entry points retain their
admission. `MakeBlindPartFromPlan` keeps its established import/call contract,
and `PartCandidate` keeps its fields. The normal adapter and public writer
registration are unchanged by this entry.

The new process regression checks two neutral documents through separate guarded
build, complete preparation and independent mathematical-comparison processes.
It includes 20 malformed complete requests per design and verifies real aliases,
parameter names/values, four unary relations, counts and allocation order.
Root's independent 4,788-path closure
`6a62fb72f8ea56cf0365c67b00609ca1e9c4d43ce48de6fcb323b455068b0025`
passes the new test and the existing blind-part, polygon-part, adapter-bridge and
host-preparation integrations. The [sanitized process receipt](../../../../re/solidworks/measurements/2026/SdkRectangleDimensions01.json) binds the retained worker reports and exact input-dependent archives. Scoped formatting, typing, steering and donor checks also pass.

Only an origin Front Plane rectangle with freely translating XY placement and
one forward blind boss is admitted. Fixed centre/corner, expressions, extra
relations, other support frames and more general features reject. The fresh SDK
native edit/save/reopen and held-out gates remain pending; earlier research
native results are not transferred to this source.

See the [field and construction ledger](../../../../re/solidworks/records/SdkRectangleDimensions2026.md)
and the [indexed-handle gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Construction/SketchHandlesReferenceValueGroups.md).

The separate exact-source mate comparison binds this same 39-path implementation in a 4,788-file closure. Its 122 guarded workers pass 660 exact stream comparisons across 12 ordered, 18 unchanged single and 12 unchanged historical bundles, plus 20 atomic negative cases. Raw result SHA-256: `0a8226b9044048835a661bd3c25f7c1d499d5d121f3fd96d2c20b9b22f11b50a`. It starts no native processes and reads no held-out inputs.
