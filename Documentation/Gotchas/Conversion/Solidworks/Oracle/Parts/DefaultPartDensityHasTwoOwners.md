# Part density preference and effective body density

An ordinary part without an assigned material has two relevant density
values. Its Definition field `f1688` stores the document material-density
preference. The 2026 settings factory initializes that preference to
1000 kg/m³. The legacy part mass getter returned a mass-to-volume ratio of
1 kg/m³ in the measured generated controls.

The first controlled trial incorrectly multiplied body volume by the
document preference and failed that check. The exact same generated parts
passed the corrected observer. In both independent designs,
`IModelDocExtension.GetUserPreferenceDouble(7, 0)` returned 1000, while
`CreateMassProperty` reported a mass-to-volume ratio of 1 before rebuild,
after edit and after fresh reopen. [Measured evidence](../../../../../../re/solidworks/measurements/2026/SdkDefaultPartNative01.json)

Check the document preference through its own API. For physical mass, use
the selected-body `IMassProperty2` path. It reported 1000 kg/m³ on the
disclosed unassigned corner control and 2700 kg/m³ after assignment. Preserve
the legacy readings with their API identity and check explicit overrides
separately. [Factory preference ledger](../../../../../../re/solidworks/measurements/2026/SdkPartPreferenceDefaults01.json) · [Selected-body diagnostic](../../../../../../re/solidworks/measurements/2026/AssignedMaterialDensityProbe01.json)
