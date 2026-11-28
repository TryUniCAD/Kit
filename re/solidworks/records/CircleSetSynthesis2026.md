# Independent full-circle sketch composition, 2026

Status: shared generative model extension; remote generation and native acceptance pending

This rung composes nonintersecting ordinary circles with separately owned centers and seam points. It uses the already bounded arc/point constructor, permanence, marker-adjacency and local-reference rules in [CircleSketchSynthesis2026.md](CircleSketchSynthesis2026.md) and [CircleAdjacencyRegistration2026.md](CircleAdjacencyRegistration2026.md). Coordinates do not imply shared node identity. Concentric, tangent, crossing, shared-point, dimensioned and body-producing sets remain outside this rung.

| Field or relation | Computation from this graph |
| --- | --- |
| Point array | Center then positive-X seam point for each requested circle |
| Arc array | One full-circle arc per request, with the same seam node at both endpoints |
| Permanence events | Start, end, center for each arc in actual arc order |
| Point creation ID | One plus the point's first occurrence in permanence events |
| Point `fe8` | Number of actual start/end/center events referencing that node |
| Point `fec` | Number of actual center roles referencing that node |
| Marker adjacency | One separate concrete handle to its own arc; second slot null under the existing equivalent-handle rule |
| Arc IDs and segment markers | One plus actual eligible arc order; no copied source IDs |
| Point/arc next counters | Actual node count plus one in each namespace |
| Sketch `f130` | Initial stamp one plus the number of actual arc permanence changes |
| Sketch `f56c` | Initial eligible segment-marker seed one plus allocations |
| Compact/full indexes | Actual point/arc owning arrays, with the existing compact saturation rule |

The caller supplies a principal plane, ordinary styles and authored provenance. Every circle is free and has independent native solver degrees of freedom. No pre-solved status, contour cache, body data or dimension display is synthesized. All output bytes flow through the existing complete common archive and compound-container emitters.

The compared process cases use two and four circles, equal-length names, the same Front plane and an identical two-circle prefix. Config-0 retains its length because the changing geometry arrays belong to the resolved stream; only the resolved stream must grow. The initial run varied name length and plane as well, so its size differences do not isolate topology. The changed native files must be measured independently, with healthy controls, before this rung counts as measured progress. The old single-circle constructor now delegates to this same composition with one member; its remote compatibility gates remain active. No held-out payload is opened and no production capability is added.

The [isolated remote receipt](../measurements/2026/CircleSetProcessesF00d6e.json) now records sixteen complete byte comparisons and strict read guards, unchanged Config-0 lengths of 21,138 and resolved lengths 6,795/7,607. The source is `f00d6ec4d`; tested merge `3b8601607` has that source and the unchanged main as independently verified parents. The downloaded artifact's digest matches GitHub's reported digest. The native-format process job passed 189 cases with 158 unrelated skips; policy process checks passed 171.

The [new native receipt](../measurements/2026/CircleSetInspection01.json) independently measures those exact two generated files with the inspector pinned to the same source. All four phases and 72 numeric/frame checks pass to six significant figures. The requested two/four ordinary circles, active sketch, initial zero-body state, geometry, frame, rebuild health, saves and fresh-process reopen all pass between healthy controls. Inputs remain immutable; the final independent process inventory finds no CAD process and unchanged licensing identities. This admits the free disjoint-circle sketch rung only. It establishes no driving dimensions, body output, complete presentation, held-out family coverage or production writing.
