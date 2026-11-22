# Read one signed angle-distance edge chamfer

Strict SOLIDWORKS part reading now returns the typed chamfer and both live drivers for a cache-free 2026 part with an ordinary rectangular Front Plane boss and one signed angle-distance edge chamfer. The two ordered selections identify the actual finite edge and the adjacent face that controls its setback. The default read reconstructs the solid from the measured triangular cut. Pass `include_brep=False` to return the same feature, parameters and selections without geometry.

Both disclosed positive and reciprocal parts pass the public read path. The reconstructed solids retain seven faces, fifteen edges and ten vertices. Independent volume, area, centre-of-mass and face-area comparisons agree to six significant figures. The existing saved-owner reader remains unchanged. Other chamfer modes and unproved presentation or geometry remain outside this path.

[Adapter guide](../../../../Reference/Adapters/Solidworks.md#writing-one-angle-distance-edge-chamfer) · [Guarded read receipt](../../../../../re/solidworks/measurements/2026/EdgeChamferPublicReader01.json)
