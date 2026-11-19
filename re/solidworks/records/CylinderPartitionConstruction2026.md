# Model-generated cylinder partition

Task `B04-SW2026-MATES-CONCENTRIC/cylinder-partition`, owner `/root`, delivery PR #121. This tranche exercises standalone active and rollback streams for the exact 2026 SP05.2 schema `SCH_3701250_37102_13006`. It follows the [saved kernel identity mapping](ConcentricKernelFaceIdentity2026.md), [fresh part identity audit](FreshCylinderEndpointIdentity2026.md), and [shared rectangular topology and allocator](GeneratedRectanglePartition2026.md).

## Disclosed source evidence

The complete typed reader and writer re-emit both partition payloads of each hash-locked D01–D03 child before and after its driving-depth edit. The six source states give twelve byte-exact payload comparisons. In each state the solid has one lateral cylinder and two planar caps, two periodic circle edges, four loops and fins, two shells, and two regions. Each loop's single fin points to itself in both traversal directions. The opposite fin points back on the same edge. There are zero stored vertices and points in either cap ring. The public B-rep decoder creates one seam vertex per circle when it projects that topology.

The `FACE_ID_2001` cap's primary lane has kind 40, cap selector 1 on the sketch plane, selector 0 on the far plane, and contour 0 on both. This physical correlation applies to the disclosed forward Front cases. The lateral lane is the actual kind-74 sketch entity relationship. [Locked source protocol](ConcentricMateArchive2026.md)

| Wire owner | Construction |
| --- | --- |
| CIRCLE 31 and CYLINDER 51 | Shared typed schema takes the field order and pointer classes from the existing active-graph reader. Two circles share the constructed cylinder's radius, support basis, and respective cap centres. |
| Boundary and surface graph | The neutral circle and its generated arc, sketch, and profile determine the world-space axis, radial basis, centre and blind extent. Cap faces use the same carrier plane normal with opposite face senses. The allocator links the two periodic rings and both shells. |
| Persistent face `node_id` | The generated topology allocator assigns an entity identifier. The actual active-payload reader returns it independently of the wire index. |
| `FACE_ID_2001` primary lane | The producing feature supplies the native feature ID and first creation epoch. The side supplies the actual sketch arc's permanent marker. The two caps supply their source-verified selectors. |
| `FACE_ID_2001` auxiliary lane | Explicit experiment session input gives the number of earlier allocation events. The shared process-counter model allocates one number per face. The six saved forward cylinder states preserve sketch-plane cap, far cap, and side order. |
| `ATOM_ID_2001` and last modifier | The model's empty atom manager supplies the next possible atom ID. The feature ID supplies the last modifier. The body attribute thus records a proposed binding that the separate attachment experiment consumes. |
| Mark graph | The caller supplies geometry and activation allocation events as explicit construction inputs. The shared mark and rollback code accounts for runtime pointer arrays separately from the transmitted graph. |

## Guarded construction and replay

The normal SDK preparation route builds two independently authored offset, forward blind Front diameter parts. The experiment generates their partition streams directly from the actual typed candidates. Six fresh host processes give two runs per case, including repeated refusal of an ordinary reverse Top radius candidate. Each accepted case repeats the projection in memory, verifies exact active and rollback bytes through the typed writer, and checks the graph, history, attributes, and the decoded public B-rep. Analytic area, volume and centre match the authored geometry. The two prior rectangle cases retain identical full measurement bytes across the shared refactor. [Process receipt](../measurements/2026/GeneratedCylinderPartition01.json)

```sh
PYTHONPATH=src:re/tooling/sw2026:re/tooling/sw2026/serial:. python -B -m para.cylinder.CheckProjection FrontDiameter
PYTHONPATH=src:re/tooling/sw2026:re/tooling/sw2026/serial:. python -B -m para.cylinder.CheckProjection OffsetFrontDiameter
PYTHONPATH=src:re/tooling/sw2026:re/tooling/sw2026/serial:. python -B -m para.cylinder.CheckProjection ReverseTop
PYTHONPATH=src:re/tooling/sw2026:re/tooling/sw2026/serial:. python -B -m para.cylinder.CompareSaved /absolute/path/to/source-packet/Disclosed
```

[Generated archive attachment](CylinderArchiveAttachment2026.md) exercises the actual archive atom, mark, and body tracking relationships at the SDK boundary. Native body and occurrence acceptance remain open. These runs credit zero native conversions and zero held-outs.
