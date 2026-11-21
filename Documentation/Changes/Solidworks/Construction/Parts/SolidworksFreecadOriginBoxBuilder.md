# Shared SOLIDWORKS origin box construction

The internal SDK now lowers an admitted FreeCAD origin box into an editable two-length profile and blind boss on the source principal plane. The shared corner anchor links the profile to the native model origin. The translated body name, driver names and literal properties use the same native owners as the measured source-label candidate.

The FreeCAD research worker calls the SDK builder with its validated neutral source and explicit native destination. The [shared build receipt](../../../../../re/solidworks/measurements/2026/SdkFreecadBoxSharedBuild01.json) records six guarded builds that reproduce both native-tested files with zero runtime reads, including two builds without the source geometry cache or stored payloads. Three further requests fail closed on a mismatched driver, foreign destination or unmapped configuration.

The proof covers one disclosed origin-fixed AdditiveBox source. Public registration and original-corpus acceptance are pending. See the [source and lifecycle record](../../../../../re/solidworks/records/SdkFreecadOriginBox2026.md).
