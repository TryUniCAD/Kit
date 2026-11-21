# A source cylinder has more than two editable owners

An ordinary full cylinder appears geometrically determined by radius and height. The actual disclosed strict FreeCAD 1.1.4 documents contain thirteen feature-owned driving parameters, complete native metadata and placement, and no authored sketch or support datum. `Body` is the FreeCAD reader's synthesized default body name, not an authored Body container.

The current SDK additionally decodes an owned analytic B-rep and native shape payload that were absent from the older strict JSON. The original FCStd bytes did not change. Deleting that B-rep, the additional parameters, property attributes or provenance to pass the plain-circle constructor would change the source contract.

Retain the full source and record explicitly derived native history separately. Bind each native dimension to the actual source driver ID and preserve the remaining source owners or refuse conversion. Keep the historical and current projection hashes distinct. The [admission evidence](../../../../../re/solidworks/records/FreecadCylinderAdmission2026.md) identifies the exact current refusal and the still-unqualified native mappings.
