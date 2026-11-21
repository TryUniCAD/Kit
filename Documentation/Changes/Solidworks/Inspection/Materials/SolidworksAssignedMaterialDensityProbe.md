# Observe material identity independently of measured density

The first two disclosed SOLIDWORKS 2026 SP05.2 source designs record the requested catalog and material name. The legacy part API reports a density and mass-to-volume ratio of 1 kg/m³. Both native controls pass.

The follow-up observer measures the disclosed corner solid through both mass APIs. The selected-body API gives 1000 kg/m³ unassigned and 2700 kg/m³ after material assignment, save and fresh read-only reopen. The legacy result remains 1 kg/m³. The two-design source lifecycle and pre-writer held-out source lock are pending. [Frozen protocol and evidence](../../../../../re/solidworks/records/AssignedMaterialSourceProtocol2026.md#first-native-result)
