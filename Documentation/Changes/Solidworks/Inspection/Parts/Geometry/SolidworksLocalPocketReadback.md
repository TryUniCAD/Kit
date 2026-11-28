# Read an imported Parasolid solid with one rectangular recess

Strict SOLIDWORKS part reads recover a closed local imported body with one
blind rectangular recess opening through its upper XY face. The reader
follows the actual feature, configuration atom, active rollback, face, loop,
edge and terminal-fin ownership. It verifies the complete directed boundary
and its plane and line carriers in millimetres before projecting the body.

Full reads include the B-rep and three native payloads. Design-only reads
keep the same import feature, body identity, and topology counts while
omitting geometry and native payloads. Neutral JSON preserves both forms.
[Design-only ownership gotcha](../../../../../Gotchas/Conversion/Solidworks/Geometry/DesignOnlyPocketOwnership.md)

Two generated parts matched all 24 frozen stream digests and both whole-file
digests. The full reads recovered the independently computed area, volume and
centroid. Both modes refused foreign storage and face owners, missing fin
rotation, a displaced plane, and a competing payload. The existing rectangle,
concave prism and two cylinders retained exact measured hashes and readback.
[Readback proof](../../../../../../re/solidworks/records/LocalPocketTopology2026.md#strict-sdk-readback)

The accepted reader profile covers one bare, unmarked local solid. Native
acceptance and per-output public publication of generated pockets still
require their own evidence.
