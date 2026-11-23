# Internal local import supports multiple circular through-bores

The shared SOLIDWORKS local body composer now derives a closed round
stock with multiple disjoint through-bores from a neutral B-rep.
Each opening has a cylindrical wall parallel to the signed principal
axis, distinct rim ownership on both caps, and positive clearance from
the stock exterior and all other openings. The strict full and
design-only readers agree on the imported feature and solid.

Two and three bores regenerate exactly across 24 streams, including
different cap orders and equal bore radii. The earlier ten cases preserve
120 stream hashes. The offline proof verifies independent mass properties,
exact neutral JSON readback and zero runtime data reads. This is an
internal geometry-only profile. Public writing requires separate
native acceptance and the output supplies an imported solid without
editable source feature history.
[Adapter scope](../../../Reference/Adapters/Solidworks.md)
· [Evidence and reproduction](../../../../re/solidworks/records/PerforatedLocalImport2026.md)
