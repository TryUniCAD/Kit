# Typed prism equality can hide display order differences

A saved Fusion cuboid can retain the same typed history and scene after
canonical encoding while its physical edge and face records change order.
The corresponding zero-LOD display leaves can still refer to the live
body and contain the expected solved bounds. An independent control can
also use a different solid display group, so matching dimensions cannot
establish that the display-leaf rule applies.

Resolve the live solid owner and a complete role-to-bound correspondence
before building the isolated history order contrast. Keep the generated
archive read-only while testing picking and per-face appearance in Fusion.
See the [saved order comparison](../../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md).
