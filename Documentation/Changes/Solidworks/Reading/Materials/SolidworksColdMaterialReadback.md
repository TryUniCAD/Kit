# Read and republish measured cold material parts

The strict SOLIDWORKS reader now projects the editable sketch, origin
constraint, forward blind depth and body-owned material for the two measured
physical material parts. The centered sketch keeps its shared point and both
construction diagonals. The full read derives the solid and the design-only
read keeps the same editable feature and material owners.

The reader checks all ten logical streams against reconstruction from the
decoded model. The standard quarter-turn camera matrices can differ by the
documented platform rounding rule. The geometry, feature and configuration
owners still pass exact comparisons. [Cold material decoding](../../../../../re/solidworks/records/AssignedMaterialColdRoundtrip2026.md)

The public writer uses the same native authority, final locator and creation
epoch for a matching readback or its JSON round trip. Both measured archives
republish byte for byte through the registry, adapter and direct writer.
[Guarded cold material round trips](../../../../../re/solidworks/measurements/2026/SdkColdMaterialRoundtrip01.json)
