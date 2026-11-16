# Mixed ordinary line/arc sketch synthesis, SOLIDWORKS 2026

Status: shared-model research construction only; exact new remote/native outcomes pending. The public adapter remains read-only. No saved field program, template, recorded payload or vendor file participates in emission.

The pre-writer [source lock](../v2026/heldout/CurveSourceLock.json) already includes discovery case `D23TangentCapsule`, SHA-256 `b74657aeb7ab7843cbb5f8af188a99374d61a9a9fed63fe752feaa25a806cc1f`. The new constructor uses geometric formulas and the documented native operations, not that document's field values. No held-out native payload is opened. This free-sketch rung does not reconstruct the discovery case's tangent/dimensional constraints or inherit its acceptance.

For neutral center `c`, radius `r`, straight length `l` and angle `a`, compute local unit directions `u=(cos(a),sin(a))`, `v=(-sin(a),cos(a))`. Arc centers are `left=c-l*u/2`, `right=c+l*u/2`. The ordered vertices are `left-r*v`, `right-r*v`, `right+r*v`, `left+r*v`. Two lines connect vertices `0→1` and `2→3`; positive semicircular arcs connect `1→2` around the right center and `3→0` around the left center. All six point nodes remain distinct and belong to the actual sketch/frame.

| Field or relation | Computation and native ownership |
| --- | --- |
| Point array | Four boundary vertices, then left/right center nodes; coordinate equality never substitutes for identity |
| Geometry arrays | Two ordinary `sgLine` nodes and two ordinary `sgArc` nodes, using the existing constructors and shared archive schemas |
| Permanence events | Actual line arrays first, then arc arrays; each segment visits start/end and each arc additionally visits center |
| Point creation IDs | One plus first role occurrence; center-array order can differ from permanence order |
| Endpoint counts | Actual role multiplicity; boundary points have two endpoint roles, centers have one center role |
| Endpoint adjacency | Distinct incident segments in their first-registration order; every retained slot owns a separately allocated concrete handle |
| Center adjacency | None; center use increments its role counters without adding endpoint handles |
| Per-type creation IDs | Actual line or arc index plus one in its own namespace |
| Segment permanent marker | One plus the actual eligible segment walk position; arc markers include the preceding line allocations |
| Compact handle/index fields | Actual owning arrays with the already proven extended-index sentinels |
| `fd0` | Derived from actual matching endpoint adjacency, checking both slots rather than assuming first-slot ownership |
| Next counters | Actual point/line/arc allocations plus one; shared marker next value uses total eligible segments plus one |
| Initial `f56c` stamp | Constructor one plus actual line/arc permanence events; later native solve changes remain separate |

The [curved construction record](CurvedSketchConstruction2026.md) establishes the shared marker walk, separate per-type creation counters, point role use, arc direction and geometry-change operation. The [adjacency record](CircleAdjacencyRegistration2026.md) establishes equivalent-target suppression before allocating a retained clone. The [polygon construction](PolygonConstruction2026.md) supplies ordinary lines and its already measured closed-ring point ownership. This implementation unifies circle/arc and mixed-curve composition in `builders/Geometry.py`; the older polygon constructor retains its existing admission and gates.

The native measurement must check actual shared endpoint identities as well as coordinates. No tangent constraint, fully constrained state, solved cache, contour list, body or dimension is fabricated. General branching, endpoint/center role mixing, circle-marker sharing and counts outside their wire widths fail closed.
