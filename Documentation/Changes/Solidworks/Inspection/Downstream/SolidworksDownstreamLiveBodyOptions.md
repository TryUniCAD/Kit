# SOLIDWORKS live downstream body options

The oracle probe reads the downstream option word from a fresh, exactly identified SOLIDWORKS 2026 SP05.2 process. It samples that word after startup, after opening a hashed native control, after rebuild and before closing the control. It opens the control read-only and leaves the option word and license service alone.

All four samples on build `34.5.2.0604` returned zero. The disclosed part rebuilt as one solid with zero open errors, warnings or rebuild issues. This is evidence for the observed control's runtime settings. Complete cache generation and native drawing acceptance are measured separately. [Probe and receipt](../../../../../re/solidworks/records/DownstreamLiveBodyOptions2026.md)
