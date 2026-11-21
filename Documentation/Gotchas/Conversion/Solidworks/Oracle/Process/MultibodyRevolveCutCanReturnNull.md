# General revolve creation can return null for multibody cuts

Three partial cut requests passed their verified sketch and axis
selections after both stocks rebuilt with measured geometry. The two
targeted requests also checked the selected body identity. The recorded
`FeatureRevolve2` cut flags returned no feature in any of the three
cases. Both independent native controls passed.

Record the actual return value and all marked selections. The vendor's
cut example uses a dedicated cut entry after marking the sketch and
axis. Use `FeatureRevolveCut2` to measure that entry independently on
the same models.
[Oracle result](../../../../../../re/solidworks/measurements/2026/RevolveCutDiscoveryFailed02.json) ·
[Vendor cut example](https://help.solidworks.com/2025/english/api/sldworksapi/Create_Revolve_Features_Example_VBNET.htm)
