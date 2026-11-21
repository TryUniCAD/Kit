# Linear pattern creation can return an empty feature after setting the definition

The disclosed SOLIDWORKS 2026 SP05.2 part used an actual principal
plane and seed boss through `D1Axis` and `PatternFeatureArray`.
The active scalars read back correctly and the second direction was
absent. `CreateFeature` returned null. The same batch's before and after
controls were healthy, and the source was never saved.

For the alternate authoring path, select the actual direction and seed
before constructing the definition. The interface uses marks 1 and 4
for those roles. Check both marked object identities, the resulting
pattern definition and the live geometry. A setter readback alone
does not establish feature creation.
[2026 API example](https://help.solidworks.com/2026/english/api/sldworksapi/Create_Bidir_Linear_Pattern_Example_CSharp.htm) ·
[Observed failure](../../../../../../re/solidworks/measurements/2026/LocalLinearPatternCreateDefinition02.json)
