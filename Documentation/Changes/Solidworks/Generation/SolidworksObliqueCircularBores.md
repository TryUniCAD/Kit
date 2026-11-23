# Local round stock supports exactly representable oblique bores

The shared SOLIDWORKS local import composer handles round stock with
several disjoint parallel through-bores at oblique orientations. The
writer and strict reader require the real cap, rim and wall coordinates
to agree in neutral millimetres and wire metres. They reject placements
that lose incidence in either representation and preserve the existing
single-cylinder, annulus and signed-axis outputs.

Two model-only parts with two and three bores reproduce 24 streams.
Their full and design-only reads retain the same solid ownership.
The earlier twelve cases retain 144 stream hashes. Public publication
still requires native measurement. The geometry-only result supplies
an imported body without editable source feature history.
[Adapter scope](../../../Reference/Adapters/Solidworks.md)
· [Verification and limits](../../../../re/solidworks/records/ObliqueLocalBores2026.md)
