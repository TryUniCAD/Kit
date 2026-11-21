# Nearly parallel supports need a line check

Distance to each selected plane can be tiny while the actual intersection line is far away. With support normals `(0, 0, 1)` and approximately `(0, 1.5e-9, 1)`, independent plane residuals can accept a segment ten millimetres away or perpendicular to the line.

Compute the normalized intersection direction and measure both endpoints against that line. Retain the dimensionless parallel cutoff of `1e-9` on the normals' cross-product magnitude. That cutoff matches the direction tolerance for stored endpoint snapshots.

Subtracting two translated float coordinates can erase a separation before summation. Take normals `(c, 0, c)` and `(c, 1.5e-9, c)`, where `c = sqrt(0.5)`, through `(0.001, 0, 0)` and `(1000.001, 5, -1000)` mm. The stored floats put the line at `y = 4.999988852752422` mm. Subtracting the rounded coordinates first puts it at `5` mm. Carry the original float values through the intersection solve as exact fractions and round the anchor at the end. [Geometry check](../../../src/interchange/Features/CheckAxisFit.py) · [Near-parallel document regression](../../../tests/Interchange/Document/PlaneAxisNearTests.py) · [Translated document regression](../../../tests/Interchange/Document/PlaneAxisShiftTests.py)
