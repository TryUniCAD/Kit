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
