# Strict reading of generated circular bosses

The default strict SOLIDWORKS reader now reconstructs a closed B-rep for the two ordinary circle profiles already emitted by the public writer: a forward Front Plane diameter-driven blind boss, or a reversed Top Plane radius-driven blind boss. It validates the complete native graph, actual fixed-centre circle, live depth and support ownership before deriving geometry. The writer bytes and destination policy are unchanged.

Use normal `open_document` with its default geometry settings. The `sldprt.brep_reconstructed` diagnostic identifies `typed_parametric_circular_boss` and records the actual profile, radial, depth and boss owners. Returned face and surface IDs belong to neutral analytic topology; they do not claim native persistent face identity. Other circle/end/support profiles remain outside this route.

[Process evidence](../../../../../re/solidworks/measurements/2026/SdkColdCircleRead01.json) records 33 fresh processes: both original failures reproduced, six positive strict circle reads, twelve malformed refusals, and three exact prior-geometry payload/document comparisons. Both real public writer payloads remain unchanged. Independent radius/depth edits match volume, area, carrier geometry, caps and bounds. Runtime data-file reads, CAD launches and hidden-input reads are zero. [Field and boundary record](../../../../../re/solidworks/records/SdkColdCircleRead2026.md).

The [cache-free read gotcha](../../../../Gotchas/Conversion/Solidworks/Geometry/CacheFreeCircleNeedsItsOwnReadRoute.md) describes the original failure. Native concentric endpoint construction and broader circle-source qualification remain separate.
