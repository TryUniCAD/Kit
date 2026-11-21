# Unused pattern directions need readback

A current installed setter declaration does not prove that a Python `VARIANT(VT_DISPATCH, None)` is accepted as an unused direction by that generated property wrapper.

In the first ordinary 2026 part-feature linear-pattern source job, `CreateDefinition`, actual seed/direction assignment and the authored D1 scalar setters succeeded. Setting `D2Axis` to that null dispatch raised COM type mismatch `-2147352571`, argument 1. It happened before `CreateFeature` and before a native source was saved. Both controls passed and the owned application exited. The [exact setup receipt](../../../../../../re/solidworks/measurements/2026/LocalLinearPatternSourceSetup01.json) is failed acquisition evidence, not a file-format crash or writer result.

For the ordinary fresh-definition protocol, omit unnecessary optional assignments. Record and require `IsDirection2Specified == false`, actual `D2Axis is null` and the returned skip collection empty before creation, then validate them again after creation/rebuild and every edit/reopen. Keep actual unused D2 scalars in the record. Do not infer persistent field defaults from this source-author policy, and do not weaken the second-direction or skip gates.

The revised packet is unexecuted at this publication boundary. Its fresh getters and complete source lifecycle still require root-owned native qualification.
