# Crease edge class and splits follow the crease angle

## Expectation

Fusion converts a cage layout with a fixed linear map. The converted body of one layout should therefore keep one edge structure, and each edge should keep one stored class.

## Actual behavior

The surfaces, curves and points follow the linear map. The crease edges do not keep one structure. Fusion 2706.1.17 stores a crease between two faces as `tangent` while the faces meet flat. It stores `unknown` once they bend, and it splits some bent creases into two edges.

`CreaseSplit.py` measured the angle between the two face normals along each creased plane crease. The sign comes from the triple product with the edge tangent.

| Archive | Largest angle | Interior sign changes | Fusion crease |
| --- | --- | --- | --- |
| 7 grip move probes | 0.052° to 0.643° | Noise near 0 | One `tangent` edge |
| Probe `RandomA` | 1.812° | 1 at 1.341 | One `unknown` edge |
| Probe `RandomB` | 6.135° | 1 at 2.401 | One `unknown` edge |
| Large move of grip 31 | 1.163° | Flat from 2.0 to 3.0 | `unknown` on [0, 2] and `tangent` on [2, 3] |
| Edit of the fresh creased plane | 3.170° | 1 at 1.5747418242971716 | Two `unknown` edges split at 1.5747418242971716 |
| Bent, sagged and fresh cages as loaded | 5.349° to 9.124° | None | One `unknown` edge |
| Acceptance edit of the vendor cage | 5.827° | None | One `unknown` edge |
| Edits of the bent, sagged and twisted cages | 5.912° to 27.706° | None | One `unknown` edge |

Fusion split one crease at the root of the dihedral function and another at the start of a flat part. It kept two other creases with a sign change as one edge. The local evidence does not fix the split rule.

The creased box crease ends at a dart. Fusion always splits its edge at the dart knot -1.0 into a `tangent` and an `unknown` piece. The shape of that layout already holds the split.

## Workaround

`ClassifyEdges` gives each edge between two faces a class from the measured angle, or refuses the cage. It samples eight interior points in each knot span.

| Measured edge | Kit class |
| --- | --- |
| Shape class `tangent`, largest angle at most 0.65° | `tangent` |
| Every angle above 1e-6 rad, largest at least 1.15°, one sign | `unknown` |
| Any other edge | `ValueError` |

`CreaseCheck.py` compared the Kit body with the converted body of every Fusion-saved archive of a body-shape layout. It compared the edge count, coedge counts, classes and split bounds.

| Result | Archives | Detail |
| --- | --- | --- |
| Accepted and equal | 431 | 13 creased plane archives needed the `unknown` class |
| Refused, Fusion split or kept a sign change | 7 | Four geometries: the fresh edit, `RandomA`, `RandomB` and the grip 31 move |
| Accepted but different | 0 | |
| Refused but equal to the shape | 0 | |

Kit could not read 13 weighted or stale probe archives, and one probe archive has no converted body. The check skipped them.

No archive has a largest crease angle inside the band from 0.65° to 1.15°, so Kit refuses that band. `SwapFormCage` keeps the stored class, so it also refuses a new cage whose class differs from the old cage.

## Evidence

- [Crease split study](../../../../../re/Fusion/Reconstruction/FormDocuments/Cages/CreaseSplit.json)
- [Crease check](../../../../../re/Fusion/Reconstruction/FormDocuments/Cages/CreaseCheck.json)
- [Cage document acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/CageDocuments/NativeAcceptance.json)
- [Probe results](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Probe.json)
