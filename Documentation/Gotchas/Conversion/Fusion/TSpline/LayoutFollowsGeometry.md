# Mixed-valence layouts change with the grip positions

## Expectation

Fusion converts each cage layout with a fixed linear map. The converted faces, edges and vertices then depend only on the cage topology. A table keyed by the topology converts every cage of the layout.

## Actual behavior

This holds for the eight layouts with stencil tables. It fails for cages that join extraordinary vertices of different valences in one band. Fusion 2706.1.17 converted two band cages under single-grip, paired and random grip moves. `LayoutDrift.py` compared the BRep layout of each saved variant with the unmoved cage.

| Cage | Grips | Variants | Base faces, edges, vertices | Variants with another layout |
| --- | --- | --- | --- | --- |
| Valence-7 prism | 44 | 55 | 21, 49, 30 | None |
| Band with valences 5 and 6 | 36 | 47 | 19, 44, 27 | `X33` with 19, 45, 28 and `RandomB` with 20, 46, 28 |
| Band with valences 7 and 8 | 48 | 59 | 25, 58, 35 | `RandomA` with 25, 59, 36 and `RandomB` with 26, 60, 36 |

A single grip move in `X33` split one more edge. The random moves also grouped the patches into another set of faces. Fusion therefore groups faces and splits edges by geometry in these cages.

## Workaround

Kit has no table for the two band cages, so `ConvertCage` refuses them. `StencilFit.py` excludes them from the fit, because no single layout holds all their variants. A future rule for these cages must predict the face grouping and the edge splits from the grips.

## Evidence

- [Layout drift](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/LayoutDrift.json)
- [Probe preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Preparation.json)
- [Probe results](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Probe.json)
