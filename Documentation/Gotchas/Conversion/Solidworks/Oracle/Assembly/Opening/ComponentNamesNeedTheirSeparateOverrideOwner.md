# Component names need their separate override owner

An authored `moReference_c` node name can be present on disk while the live assembly reports a dependency-derived name through both `IFeature.Name` and `IComponent2.Name2`. A strict comparison must retain that loss instead of changing its expected name.

In the exact 2026 build, actual user-overridden reference IDs also have a signed set in the configuration manager. The lightweight header transfers that set, but its ordinary `Contents/CMgrHdr2` CArchive layout does not serialize it. A separate UnQLite stream, `Contents/3DExperienceExchange_ConfigHeader`, carries the MessagePack `overriddenReferenceIDs` owner. Putting a new flag into the old header grammar would corrupt the proved layout.

The reference pass-two override-bit recalculation is DotWorks-mode gated. The ordinary synchronization has additional environment and external-object predicates. The separate persisted owner is confirmed; it is not yet a native fix for the current generated parent. Trace the actual load branch and measure an independently authored custom-name control before constructing that owner. Keep global preferences unchanged unless separately authorized.

[Source rule and limits](../../../../../../../re/solidworks/records/ComponentNameOverrideStorage2026.md) · [Native name observation](../../../../../../../re/solidworks/measurements/2026/ConcentricReferenceNamesNative01.json)
