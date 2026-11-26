# Fusion configuration member order can differ from serializer order

The saved baseline, restore and previously reserved cuboids store the empty configuration table before the rule. The saved edit stores the rule before the table. The Design segment places the table trigger before the rule trigger in all four files, and each trigger refers to its own independently named member.

Use the [configuration request](../../../../../Changes/Research/Encoder/FusionSavedConfigEnvelope.md) to carry member order explicitly. Link every generated member to its matching root by role. The observed empty objects describe the structural envelope of an unconfigured document. Configured designs require separate semantic rules and evidence.
