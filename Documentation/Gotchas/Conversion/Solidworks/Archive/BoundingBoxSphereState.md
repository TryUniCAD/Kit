# Bounding boxes store sphere state before their corners

A SOLIDWORKS 2026 `mgBBox_c` archive record is ten doubles, not six ordered
minimum/maximum coordinates. It stores center XYZ, high corner XYZ, low corner
XYZ, then sphere radius. Reusing a six-value AABB layout shifts every later
field; zero fill loses the computed state.

Static `sldmgu.dll!0x31e02820` restore and `0x31e03790` save prove the wire
sequence. High/low accessors `0x31de5980` and `0x31de71b0` identify the corner
owners. Point-pair constructor `0x31ddcf60` and setter helper `0x31de85b0` derive
the center as the midpoint and the radius as half the Euclidean diagonal.
These rules come from native instructions, not values sampled from saved files.

The default constructor `0x31ddd2c0` intentionally creates an unset box: center
zero, high minus one, low plus one and radius minus two. `isSet` at
`0x31de6ae0` rejects negative radius or reversed bounds. That seed is not proof
that an invalid box is an accepted neutral saved cache.

Compute the record from actual semantic geometry and preserve cache ownership.
The [assembly construction record](../../../../../re/solidworks/records/AssemblyConstruction2026.md)
contains the module hash, exact mapping, constructor API and unresolved cache
policy. The rule does not establish target-application acceptance by itself.
