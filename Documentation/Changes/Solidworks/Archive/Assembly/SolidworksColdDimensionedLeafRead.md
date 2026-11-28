# SOLIDWORKS cold dimensioned leaf read

The strict SOLIDWORKS part reader now opens the cache-free Front-plane rectangular blind-boss leaves emitted by the rigid nested assembly writer. It retains the two sketch lengths, four axis relations, two point-distance relations and true forward depth. Native label points and routing flags stay on the corresponding sketch relation. The three parameters retain their separate native owners, including both occurrences of the label `D1`.

Use ordinary `open_document` for the parametric leaf and its analytic solid. Use `include_brep=False` to read the same sketch and feature data without building the solid. The reader rejects contradicted owner, reference-count and extrusion state. The measured scope is the single-configuration local rectangle and forward blind boss used by the assembly writer.

The three disclosed dimensioned leaves and one plain control reproduced the linked ResolvedFeatures streams. The strict SDK views match the existing native driver values, topology, volume, surface area and centre of mass. Five typed ownership and draft contrasts failed closed with and without B-rep. [Reproduction and limits](../../../../../re/solidworks/records/NestedDimensionedLeafRead2026.md)
