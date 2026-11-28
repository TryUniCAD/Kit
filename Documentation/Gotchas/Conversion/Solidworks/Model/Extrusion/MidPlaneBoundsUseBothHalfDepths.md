# Mid-plane stock bounds use both half-depths

A typed mid-plane extrusion stores its full depth. In the geometry-disabled reader, placing that depth entirely on one side of the datum shifts the body summary by half the depth. The saved active solid in all three measured principal-plane examples reaches equally far on both sides.

Project the stock profile from its actual support along the signed offsets `-depth/2` and `+depth/2`. Compare the result against the active saved solid when qualifying the body footprint. [Measured bounds](../../../../../../re/solidworks/measurements/2026/MidPlaneStockBounds01.json)
