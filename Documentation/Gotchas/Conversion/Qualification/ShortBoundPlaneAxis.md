# Short bound axis direction comes from its stations

Subtracting two rounded model points at a large offset can magnify a tiny position error into a failed angular check. A 0.01 mm axis through `(1000000, 0, 0)` mm in direction `(0.6, 0.8, 0)` has a rounded endpoint about `4.17e-11` mm off the line. The rounded segment direction differs by about `4.17e-9`, above the `1e-9` angular tolerance.

Use the ordered signed stations to establish the direction of a bound segment. Verify both generated points remain finite, distinct, and on the intersection within the position tolerance. Keep the angular check for authored snapshots, whose point pair supplies their direction. [Ordinary document regression](../../../../tests/Interchange/Document/BoundAxisSpanTests.py)
