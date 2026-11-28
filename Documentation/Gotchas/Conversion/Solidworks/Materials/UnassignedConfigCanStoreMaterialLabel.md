# An unassigned configuration can store a material label

The pristine SOLIDWORKS 2026 control's configuration visual record stores the string `Steel`. Its part density parameter is 1,000 kg/m³, the configuration density override is `-1`, and the material tree is absent. Fresh source designs report a blank assignment in the API before the explicit material operation.

Verify the actual configuration assignment and physical density before interpreting a saved label. The disclosed named assignments carry exact catalog and material IDs and set both binary density owners. [Controlled comparison](../../../../../re/solidworks/measurements/2026/AssignedMaterialArchiveOwners01.json)
