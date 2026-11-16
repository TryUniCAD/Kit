# Ordinary open-arc synthesis, SOLIDWORKS 2026

Status: constructor-derived free-sketch research rung; remote generation and native measurements pending. No source or held-out native payload was read to build this extension.

The [original curved-entity construction record](CurvedSketchConstruction2026.md) supplies the concrete `sgArc` constructor at `0x4b92df10`, serializer `0x4c585150`, local normal selection, direction reversal and endpoint/center roles. The [adjacency record](CircleAdjacencyRegistration2026.md) supplies equivalent-handle comparison and separate retained-clone allocation. Common point/segment/profile fields retain their existing constructor ownership; no solved status or derived cache is fitted from a saved arc.

| Field or relation | Rule for this fresh, otherwise unconnected arc |
| --- | --- |
| Geometry input | Local center, positive radius, start angle and signed partial sweep in radians |
| Start/end positions | `center + radius * (cos(angle), sin(angle))`, at start and start-plus-sweep |
| Node identity | Three distinct ordinary points in center/start/end array order; reject numerical coincidence |
| Circle predicate | Endpoint node identity differs; full circles instead deliberately reuse one endpoint |
| `fd8` | `+1` for a positive local sweep, `-1` for negative; native orientation vocabulary is bounded to signed unit direction |
| `fc8/fcc/fdc` | Actual start/end/center indexes; compact selectors derive through the shared sentinel rule |
| `fd4`, `seg_tol`, `fe0/fe4/fe8/fec` | Existing ordinary nonflipped, absent optional-scale/normal/fillet/virtual-point constructor rules |
| Permanence role sequence | Start, end, center; these distinct nodes receive creation IDs one, two, three |
| Point-use counts | One use for each endpoint and center; only the center has one center role |
| Endpoint adjacency | One separately allocated concrete handle per endpoint, both targeting the actual arc; both second slots remain absent |
| Endpoint point type | Ordinary type zero; the full-circle-only type-two seam marker is not applied |
| Arc ID/permanent marker | First actual arc allocation in each respective namespace |
| Next counters | Actual three point allocations and one arc allocation; no feature-family value table |
| Initial geometry stamp | Constructor one plus the actual arc-permanence event; later native solves remain separate |

Native direction and the semantic trigonometric sweep convention still require their new oracle measurement. The shared arc node, permanence walk and array composer also serve existing single-circle and disjoint-circle requests, whose remote compatibility checks remain required after the generalization. Open-arc bodies, dimensions, shared endpoints, construction entities, explicit normals and later reversal histories are refused rather than approximated.

The local-reference guard now admits constructed ordinary arcs with actual endpoint/center ownership, null external pointers and no explicit normal. The complete external scanner `[0x4b94f7e0,0x4b95055a)` and independent inter-component predicate `[0x4c6fcfc0,0x4c6fdea2)` already establish that their local-arc exits do not depend on endpoint equality, radius or orientation. The earlier builder's circle-only guard was narrower than that recorded native branch. All auxiliary-geometry, dimension and nonlocal guards remain active; this extension adds no general reference or constraint admission.

The [new remote receipt](../measurements/2026/OpenArcProcesses61622d.json) now records sixteen complete primary/linked byte comparisons and strict file-read guards. Source `61622d1a5` passed 190 native-format process cases with 158 unrelated fixture skips and 171 policy cases. The independently downloaded ZIP digest matches GitHub's reported digest; tested merge `fe1f4a4f6` has the source and unchanged main as verified parents.

The [controlled native receipt](../measurements/2026/OpenArcInspection01.json) then passes both exact generated inputs through all four phases and 64 numeric/frame checks to six significant figures, including positive minor and negative major sweeps, both endpoints, native direction, active sketch, rebuild, save and fresh reopen. Both original controls pass; inputs remain immutable; an independent postflight finds no CAD process and unchanged licensing identities. The preflight transport failure is retained separately from the successful retry. This proves the bounded free-arc rung, not a constrained arc, closed profile, body, held-out family or production writer.
