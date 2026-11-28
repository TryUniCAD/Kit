# SOLIDWORKS imported body source geometry

The research projector recovers a geometry-only neutral prism from a strict
SOLIDWORKS part read. It requires one actual native import feature, one
active configuration and one closed axis-aligned rectangular solid with
matching corners, analytic lines, face planes and oriented trims. The
projector returns the verified import feature and configuration names.
It generates the neutral geometry for the local BODY builder without
reading files during projection. [Usage and verification](../../../../re/solidworks/records/ImportedBodySourceGeometry2026.md)

Four disclosed imports produced measured local BODY geometry. The two
renamed controls used the same kernel bytes as the original. A different
shape changed the bytes. Two offline processes emitted identical receipts.
The parametric control and 16 invalid variants were refused. Source body
and part labels, material, appearance, other tree entries and native
metadata remain outside this geometry projection. The recorded acceptance
covers offline geometry and the kernel codec.
[Measurements](../../../../re/solidworks/measurements/2026/ImportedBodySourceGeometry01.json)
