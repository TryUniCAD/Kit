# Read a saved cuboid face appearance

The strict Fusion reader now accepts the fixed-corner, one-sided XY
cuboid with one saved face appearance. It verifies the Design body
and compute references, reciprocal journal attachment, full face
selection recipe, and linked Protein appearance. When the OGS
world is present, the displayed leaf must belong to the same live
body and physical face. Rollback history, snapshot and ownership
checks preserve the original parametric extrusion.

Use `kit decode Styled.f3d --output Styled.json` or the strict SDK
reader. The output keeps the full styled state in
`fusion.native_state`. The neutral body retains its material. The
neutral format has no typed per-face appearance, so that appearance
remains in the Fusion state. This saved-profile route stays read-only.

The native plain, top-red and side-red controls and the same-source
top-red archive without OGS passed strict SDK and CLI JSON readback.
All four retained the observed 6133.272 mm³ body volume. The verified
results include exact typed state after JSON persistence, two invalid
recipe or ownership refusals, and 24 writes that refused while
preserving occupied paths, streams and absent parents. All 58 existing
focused integration cases passed on Windows Python 3.14.6.

Independent native validation of generated styled output, viewport
picking and editable saved-source publication remain open.
[Styled reader evidence](../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#strict-styled-cuboid-projection)
