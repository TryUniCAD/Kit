# Bare box import needs exact face stations

The eight Cartesian corners of a rectangular input identify its extent.
A planar face also carries its own plane location. The shared prism
compiler allows small reconstruction residuals. A plane shifted by
`2^-34 mm` can pass its residual check while all eight corners and the
face, edge and vertex counts remain identical.

For the bounded bare box write, check each signed unit normal and its
exact plane coordinate against the vertices in the actual linked face
ring before invoking the shared prism constructor.
[Guarded displaced-plane contrast](../../../../../../../re/tooling/sw2026/imported_body_source/VerifyPublicBox.py)
· [Write scope](../../../../../../Changes/Solidworks/Construction/Parts/SolidworksBareRectangleImport.md)
