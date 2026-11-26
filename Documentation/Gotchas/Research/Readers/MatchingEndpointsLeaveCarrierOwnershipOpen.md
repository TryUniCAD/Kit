# Matching endpoints leave curve carrier ownership open

The saved P03 derivative and the independently vendor-edited 12 mm P03
control have the same 12 physical endpoint pairs. The vendor control's
complete typed graph ties those edges to direct line carriers. The
derivative includes a trimmed record whose stored interval on a line
reproduces one of the measured edges, but the typed read stops before it
can establish an edge consumer for that record.

Compare geometry and ownership independently. Match ordered endpoints to
the basis first, then use the actual typed edge references and a complete
graph to decide whether an edge consumes the trim. Keep the next
unsupported record in the evidence when the walk stops.
[Saved P03 trim evidence](../../../Changes/Research/Solidworks/SolidworksSavedTrimmedCurveResearch.md)
