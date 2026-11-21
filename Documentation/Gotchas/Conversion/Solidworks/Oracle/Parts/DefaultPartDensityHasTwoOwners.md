# Part density preference and effective body density

An ordinary part without an assigned material has two relevant density
values. Its Definition field `f1688` stores the document material-density
preference. The 2026 settings factory initializes that preference to
1000 kg/m³. SOLIDWORKS' mass API calculates the effective density for an
unassigned body as 1 kg/m³ in the measured profile.

The first controlled trial incorrectly multiplied body volume by the
document preference and failed that check. The exact same generated parts
passed the corrected observer. In both independent designs,
`IModelDocExtension.GetUserPreferenceDouble(7, 0)` returned 1000, while
`CreateMassProperty` reported a mass-to-volume ratio of 1 before rebuild,
after edit and after fresh reopen. [Measured evidence](../../../../../../re/solidworks/measurements/2026/SdkDefaultPartNative01.json)

Check the document preference through its own API. Check mass and effective
density from their measured body values. Material assignment and explicit
overrides require separate verification. [Factory preference ledger](../../../../../../re/solidworks/measurements/2026/SdkPartPreferenceDefaults01.json) ·
[SOLIDWORKS mass API remarks](https://help.solidworks.com/2025/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~GetMassProperties.html?format=P&value=)
