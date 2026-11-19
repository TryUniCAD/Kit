# Cap selectors need operation-end ownership

A cap's world coordinate or its position in a face array can look like the native extrusion-end selector. Those are different domains.

The existing forward rectangle cache projection uses z == depth as its local cap role. The six disclosed circular-child saves associate actual moEndFaceSurfIdRep_c.f38 in the opposite physical direction: sketch plane one, far cap zero. The exact 2026 constructor preserves its caller's selector, and the later cap callback preserves the old temporary selector while resolving contours. Neither rule derives selector from world Z.

Retain a distinct geometric role and trace its native operation-end association before constructing the identity. Do not swap every selector globally from this observation. Reversal, two directions, offsets and other end conditions still require their actual producer/consumer paths. Keep the module-static auxiliary face-ID allocator separate from the feature persistent-ID allocator and kernel node/transmit indexes.

This is a static/observed boundary correction, not a writer fix or native acceptance.

[Bound rule and remaining edge](../../../../../../re/solidworks/records/OrdinaryExtrusionCapIdentity2026.md)
