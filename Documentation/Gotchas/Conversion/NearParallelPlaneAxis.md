# Nearly parallel supports need a line check

Distance to each selected plane can be tiny while the actual intersection line is far away. With support normals `(0, 0, 1)` and approximately `(0, 1.5e-9, 1)`, independent plane residuals can accept a segment ten millimetres away or perpendicular to the line.

Compute the normalized intersection direction and measure the segment and both endpoints against that line. Retain the dimensionless parallel cutoff of `1e-9` on the normals' cross-product magnitude. That cutoff matches the direction tolerance. [Geometry check](../../../src/interchange/Features/CheckAxisFit.py) · [Ordinary document regression](../../../tests/Interchange/Document/PlaneAxisNearTests.py)
