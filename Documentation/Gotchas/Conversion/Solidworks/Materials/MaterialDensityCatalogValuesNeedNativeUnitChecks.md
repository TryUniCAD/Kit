# Material catalog density needs its actual XML owner and native units

Expectation: installed material density is a child value and the installed XSD can be parsed by the host standard parser, so an XML number can immediately become a qualified SI density.

The pinned 2026 model-free metadata capture observed `physicalproperties/DENS/@value`, with no child value, in all three installed databases. The original capture preserved the actual attributes but left its child-derived `raw_value` blank; deduplication on that blank value also retained only one entry per database. Keep that original result unchanged. Read the actual attribute and bind its database/hash identity; do not replace it with an inferred or observed mass value.

The installed material XSD is hashed, but Python ElementTree rejected its bytes at line75/column2. That observation does not prove the native parser will reject the schema or that a material database is invalid. The exact encoding/markup condition and native validator behavior remain open.

Use a predeclared density-unit hypothesis, actual native density with `UseSystemUnits=True`, independently computed analytic volume and native mass response. A material swap at fixed geometry and a dimension edit at fixed material must both satisfy their separate mass ratios. Reject a disagreement and retain it; do not fit a new conversion factor to force the source trial to pass.

The [model-free metadata receipt](../../../../../re/solidworks/measurements/2026/AssignedMaterialCatalogMetadataNative01.json) records one clean native process with zero model documents. The [source protocol](../../../../../re/solidworks/records/AssignedMaterialSourceProtocol2026.md) defines the pending material/edit/save/reopen trial and original-lock boundary. No source/model or generated material writer acceptance is established by the metadata query.
