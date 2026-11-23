# Model an imported solid with one rectangular through-opening

The internal SOLIDWORKS composer accepts a closed rectangular solid with
one enclosed straight rectangular passage between its opposite XY caps.
Each cap retains its authored outer and inner trim order. The compiler
uses the same resident body, face, edge, loop and fin rules as the blind
recess. It verifies one matching opening footprint at both cap stations
and every connecting wall before assigning wire identities.

The strict part reader validates the same shape and BaseBody ownership.
Full reads preserve both caps and their ring order in the B-rep. Design-only
reads preserve the same body and topology counts. Both projections survive
neutral JSON serialization. Two independently modeled outputs produce
deterministic whole archives and 24 stream fingerprints. Four unsupported
neutral configurations and 20 strict reader contrasts refuse. The two
earlier blind cases and four measured prism and cylinder controls retain
exact prior results. [Offline proof](../../../../re/solidworks/records/PlanarThroughOpening2026.md)

Public output still requires exact native acceptance evidence. Multiple
openings, curved passages and oblique passage axes remain outside this
profile. [Cap order gotcha](../../../Gotchas/Conversion/Solidworks/Geometry/ThroughCapsHaveIndependentLoops.md)
