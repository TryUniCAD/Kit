# Publish the two measured SOLIDWORKS planar imported solids

The geometry-only fallback publishes the exact measured rectangular
prism and orthogonal concave L prism. Each input is one closed,
outward-facing solid in millimetres with one active root
configuration. The shared constructor produces the local Parasolid
body and the native `Imported geometry` feature from the neutral
boundary. Only the measured concave profile uses the five attributes
bound to the generated body atom, feature and creation stamp.

Pass the parsed [completed native report](../../../../../re/solidworks/measurements/2026/GeneratedLocalBodyPartCompleted01.json)
in `values["solidworks_native_measurement"]["receipt"]` with
`written_at` set to `1790000000`. An empty binary stream uses the
measured `final_destination` for its case. A filesystem destination
uses the actual measured Windows path. Both routes require an exact
match of the complete archive size and digest before writing.

The result claims the two measured native transfers, B-rep and
configuration, and reports unavailable editable history. Existing
parametric routes keep their own admission and receipts. Alternate
geometry, unknown source owners and unmatched measurements refuse.

Independent host verifiers reproduced both disclosed complete archives,
all 24 stream digests and the existing Skew and Step editable outputs.
The two historical Windows receipts record filesystem publication of
those same archives. [Qualification and reproduction](../../../../../re/solidworks/records/ImportedBodyFallbackBoundary2026.md#exact-measured-planar-publication)
