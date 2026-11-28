# Resizing a free rectangle does not preserve its centre

A rectangle can initially be centred at the origin while its constraints define only horizontal/vertical edges and width/height. That geometry does not establish a persistent centering constraint.

The disclosed perpendicular source attempt resized the native rectangular seed from 40 × 20 mm to 37.9 × 16.7 mm. Volume and area matched the requested new shape, but its centre moved to `(1.05, -1.65) mm`. The unchanged zero-centre prediction correctly rejected the source. Healthy native controls bracketed the failure.

Author the intended location explicitly through the native API and verify the actual sketch coordinates before measuring the solid. The corrected source method requests the original lower-left coordinate and checks all four corners. Do not compensate a predicted centroid with a value fitted to the failed observation, or relax the native geometry gate. That explicit point-setting method still needs its own controlled native proof.

[Exact failed-source receipt](../../../../../../re/solidworks/measurements/2026/PerpendicularMateSourceAttempt01.json) · [Correction protocol and limits](../../../../../../re/solidworks/records/PerpendicularMateSourcePosition2026.md)
