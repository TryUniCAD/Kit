# SOLIDWORKS component base-name source retry

The previous native source-author attempt passed the selected-occurrence checks and temporary preference readback, then recorded `AuthoredAxisA-1-1` instead of the unchanged authored target `AuthoredAxisA-1`. Both controls passed and the actual original preference was restored. This result remains a failure.

The research successor passes a base string through the exact registered `IComponent2.Name2` setter and retains the original full-name and ordinal checks. It records matched `IFeature.Name` and component `Name2` before and after each setter, before enforcing the predicate. The existing durable preference lease, restoration, geometry/ownership checks and fresh reopen under the original setting are reused unchanged.

Use `FreezeCustomComponentBaseName01.py` with the prior exact packet, original independently frozen prediction, numeric source record and unused host/guest output roots. The resulting recipe contains host and guest verification, four serial native phases, summary and idle-only recovery commands. The root oracle owner executes native phases after source publication.

The exact source replay checks three licensed original images, 13 complete function groups, six data spans and six virtual cells. Host verification checks 53 frozen files and reproduces both original 25-row prediction trees.

On 2026 SP05.2, both native interfaces reported the expected custom name for each live component. The child and parent saved cleanly. The two controls passed and the preference was restored. On fresh reopen under the original setting, both interfaces reported filename-derived names for the same two occurrence IDs. The strict source lifecycle failed at that gate. Writer and public acceptance remain open.

[Source rule and usage](../../../../../re/solidworks/records/ComponentBaseNameSetter2026.md) · [Host receipt](../../../../../re/solidworks/measurements/2026/CustomComponentBaseNameRetryHost01.json) · [Native receipt](../../../../../re/solidworks/measurements/2026/CustomComponentBaseNameRetryNative01.json) · [Instance-suffix gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/Assembly/Opening/ComponentNameSetterTakesBaseBeforeInstanceSuffix.md) · [Fresh reopen gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/Assembly/Opening/FreshOpenCanRestoreComponentFilenameBase.md)
