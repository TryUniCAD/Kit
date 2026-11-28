# Check circular bore clearance in the stored units

The neutral model uses millimetres and the Parasolid local transmit uses
metres. A binary64 conversion can change whether two circles touch.
An 18 mm outer radius and 4 mm bore have positive clearance just below
a 14 mm centre displacement. The verified nearest lower binary64
displacement becomes exactly tangent after metre encoding. In the other
direction, stored radii of 0.0065 m and 0.002125 m and a tangent
displacement of 0.0043749999999999995 m appear separated after the SDK
projects them into millimetres.

Resolve the actual cap-to-wall ring pairs first. Compare squared distances
using the exact represented coordinates and radii at each boundary.
Check native metres before decoding coordinates into neutral millimetres.
A bore must have positive clearance from the exterior wall and all other
openings.
[Both rounding contrasts and typed owners](../../../../../re/solidworks/records/PerforatedLocalImport2026.md)
