# Strict round trips for measured imported solids

A full strict read of either measured local import can return to the normal
SOLIDWORKS writer. The two profiles are the translated rectangular solid and the
owned concave L prism. Pass the strict document, or its neutral JSON readback,
with the same import measurement receipt, epoch and native destination used
for fresh publication. The stream and Windows path destination rules apply.

Kit generates the local Parasolid transmit and the complete part from the
neutral B-rep and active configuration. Before publishing, it checks the
complete digest against the native receipt and compares the strict source
projection with a read of the regenerated part. Body ownership, topology,
support planes, feature tree, physical payloads and source metadata therefore
survive this round trip. The writer emits the existing diagnostic for
unavailable editable history on an imported solid.

Design-only reads lack the solid required for generation. A changed body,
extra source property, mismatched source witness or unmeasured output refuses
without writing. The geometry-only construction route keeps its previous
options and transfers.

The isolated proof reproduces both measured containers through the registry,
writer and adapter, with zero runtime reads. Both solids match their recorded
native volume, area and centre of mass. Fresh SOLIDWORKS lifecycles, additional
held-out cases and original FCStd conversions remain pending.

[Writer guide](../../../../Reference/Adapters/Solidworks.md#preparing-a-geometry-only-imported-solid)
· [Round-trip evidence](../../../../../re/solidworks/records/SdkColdImportRoundTrip2026.md)
