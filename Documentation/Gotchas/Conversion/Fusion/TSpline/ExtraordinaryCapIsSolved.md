# Extraordinary-vertex caps come from a solved system

## Expectation

Fusion converts a T-spline cage to the Catmull–Clark limit surface away from extraordinary vertices. A converter could then add a fixed cap mask for each valence. Kit would convert any cage with valences 3 to 8.

## Actual behavior

Fusion 2706.1.17 matches the Catmull–Clark limit only outside a cap region. `CapStructure.py` evaluated four stencil tables as grip coefficient vectors and compared them with the Catmull–Clark limit of the same cage. Each cell with an extraordinary vertex at a corner has three knot spans per direction. Span 2 covers the half of the cell away from the vertex.

| Layout | Valences | Regular cells | Far quarter of the cell (span 2, 2) | Rest of the cell |
| --- | --- | --- | --- | --- |
| Box | 3 and 4 | 0 | 3.3e-16 | 2.9e-4 to 6.2e-3 |
| Box with 3 × 3 faces per side | 3 and 4 | 1.5e-14 | 2.7e-15 | 2.9e-4 to 6.2e-3 |
| Valence-5 prism | 3, 4 and 5 | 0 | 1.0e-15 | 1.5e-4 to 6.2e-3 |
| Valence-7 prism | 3, 4 and 7 | 0 | 1.8e-15 | 1.5e-4 to 6.2e-3 |

The cap changes every Bézier pole of the spans next to the vertex. It also changes the first pole row of the spans beyond them.

Static analysis of `libtsplines.14.dylib` shows how Fusion builds the cap. The dispatcher at `0x30ccdc` calls the G1 cap routine at `0x3193e4`. That routine reads `cos(2π/n)` and `cos(π/n)` for valence n. It reads poles of the neighbouring sectors and fills sparse matrix triplets. Two unnamed sparse routines at `0x790e48` and `0x79bc18` then solve the system. The fitted valence-3 coefficients are rationals whose denominators contain 1691 = 19 · 89 and 199. A fixed mask would not give such denominators.

Kit did not rebuild the matrix or the solver. The solver carries no symbols, so it is unknown whether it solves a square system or a least-squares problem. A second G1 path at `0x3139f0` and `0x325fa8` has about 15,000 decompiled lines.

## Workaround

Keep one fitted stencil table for each cage layout. `ConvertCage` refuses a layout without a table with `Fusion Form conversion has no stencil for this cage layout`. The fourth pass added the valence-7 prism to the tables. A table key is the topology, so a new layout needs a new native probe and fit.

## Evidence

- [Cap structure](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/CapStructure.json)
- [Stencil tables](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/StencilTables.json)
- [Cap function map](../../../../../re/Fusion/External/ReverseEngineer/README.md)
- [Cap trace strings](../../../../../re/Fusion/External/ReverseEngineer/libtsplines.14.strings-captrace.txt)
