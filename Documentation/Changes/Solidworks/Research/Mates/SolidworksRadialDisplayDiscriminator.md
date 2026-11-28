# SOLIDWORKS radial assembly display-state discriminator

The research preparer builds two radial assemblies at the same final
locators with one identical generated child. The variant adds two mixed
visibility states to the parent instance tree and typed VisualStates.
The baseline and variant preserve the same concentric mate, reference
stamps, header locators and eleven other parent streams.

The preparation verifies the earlier native pair's exact digests and
performs six guarded builds with zero construction file reads. The
frozen recipe passed 168 numeric checks through named visibility,
a driving depth edit and a paired save and reopen. Both native controls
passed. The generated child opens without its own VisualStates store
and receives one when SOLIDWORKS saves the edited child.

[Preparation and native procedure](../../../../../re/solidworks/records/ConcentricRadialVisibilityDiscriminator2026.md)
· [Native result](../../../../../re/solidworks/measurements/2026/ConcentricRadialDisplayNative01.json)
· [Child save behavior](../../../../Gotchas/Conversion/Solidworks/Assembly/Mates/NativeSaveCanPublishChildVisuals.md)
