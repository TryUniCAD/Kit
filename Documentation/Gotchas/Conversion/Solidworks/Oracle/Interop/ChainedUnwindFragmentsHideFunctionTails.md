# Chained unwind fragments contain function tails

The pinned 2026 `moEndSpec_c::setISurfRef` has a 36-byte primary exception-directory range. Two chained ranges contain the array update and return. `getRefWrappers` has six chained ranges and a sixteen-byte primary range.

Follow `UNW_FLAG_CHAININFO` to the primary owner and collect each associated fragment. Record the address intervals and their hashes separately. [Exact ranges](../../../../../../re/solidworks/records/FreecadCylinderDirectionWire2026.md)
