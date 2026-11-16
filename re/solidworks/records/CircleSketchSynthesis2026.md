# Single-circle sketch construction, first synthesis rung

Status: constructor-derived research graph with two remote guarded process candidates; native measurement pending. No circle-family or production writer acceptance is established.

The target remains SOLIDWORKS 2026 SP05.2, executable `34.5.2.0604`. The [curve construction record](CurvedSketchConstruction2026.md) binds original model module SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, native constructors, complete serializers, array ownership, handle encoding, local-reference scanning and ID/stamp operations. The [adjacency record](CircleAdjacencyRegistration2026.md) closes deduplication independently of observed source rows.

## Explicit graph policy

The neutral input supplies center `c`, positive radius `r`, principal-plane frame and ordinary document/style/provenance inputs. The builder computes marker `m=(c.x+r,c.y)` and rejects nonfinite or indistinguishable coordinates. This is an explicit positive-X seam policy, not a claim about every public COM authoring path or a required saved seam angle.

The point array contains distinct nodes `(center, marker)`. The arc stores the same marker node as start and end and the actual center node as center. Its local orientation is the constructor's positive orientation. An optional explicit normal, fillet-line references, virtual point, external geometry, construction geometry and later reversal are excluded.

| Field or relationship | Construction rule and evidence |
| --- | --- |
| Common entity fields and point payload | Shared `entity_fields` and `ordinary_point`; native constructors `0x4c3e1030`, `0x4c490970` and existing profile/curve records |
| Arc endpoints and center | Actual point-array positions, compact selector `min(index,0xffff)`; native `0x4b92df10`, `0x4c590920`, `0x4c585150` |
| Arc orientation and optional references | Orientation one; absent normal/fillet/virtual references `-2`; no scale cache encodes `-1.0`; all from the documented ordinary fresh constructor |
| Marker type | Point type two, with ordinary point-array discriminator zero and the positioned-point mask; point type is independent of that discriminator |
| Point-use counts | Actual permanence roles `(start, end, center)`; marker two total uses and zero center uses, center one of each; native `0x4c5635e0`, `0x4c602c10` |
| Adjacency | One separately allocated concrete arc handle in marker `h1`, null `h2`; center has no endpoint adjacency; native equivalent-handle registrar, not a two-clone assumption |
| Point creation IDs | Start-marker first use, repeated end reuse, then center; IDs are generated from that first-permanence order, independently of point-array positions |
| Arc creation ID and permanent marker | Computed from the current one-arc graph and its admitted segment marker allocation; these namespaces remain distinct |
| Next counters and pre-solve stamp | Point/arc creation counters follow actual allocated nodes; next permanent marker follows eligible segment allocations; stamp starts at one and adds the single arc-permanence change |
| Local-reference state | The complete native scanner admits nonderived ordinary permanent points/arcs with valid local ownership and null `ext`; other curve types and nonlocal bindings still fail closed |

Every count and reference follows from nodes and operations. The builder retains symbolic references and lazy derived fields through the shared archive model. No native payload or saved field program is read during emission.

## Incomplete acceptance

The new graph has no fixed-center constraint or radial value/display dimension. It is an ordinary unconstrained circle sketch, with no extrusion feature or body claim. The known single native arc is not flattened into a polygon or imported body.

Entity color/status `f30/f34` and sketch `f128/f12c` retain their documented constructor states. Their saved neutrality, complete solve/stamp effects, native profile scheduling and application behavior must be established independently. Current source graphs and prior polygon rebuilds cannot establish those circle results. Native measurements must record load/rebuild state, exact circle geometry, feature tree, controls, save and fresh reopen before advancing this family up the synthesis ladder.

The source family was locked before this code. All six held-out payloads remain unopened. The [first remote process receipt](../measurements/2026/CircleSketchProcesses814f5f8.json) binds two independent authored centers/radii, both principal planes, sixteen complete archive comparisons, file-read guards and exact generated hashes. The source revision is `814f5f82e0e8ac57a4b45f27193ca68fd17e01ef`, tested merge `927b55cb26ef30996270ade05fed48bcaf7836bf`; both parents were checked against GitHub. Native application behavior remains unqualified until controlled load, rebuild, geometry, save and fresh-reopen measurements exist.
