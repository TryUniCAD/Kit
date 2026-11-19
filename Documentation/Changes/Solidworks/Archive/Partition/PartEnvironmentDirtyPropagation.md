# Part environment dirty propagation

The SOLIDWORKS 2026 post-load path adds default lights when an ordinary part has none. The native trace follows the ambient light into the environment folder and observes the resulting transition of the part's update flag from clear to set.

Original PE replay verifies the reload condition and actual virtual calls. In the extended native probe, both ordinary controls opened cleanly with one body. The generated part reproduced warning 32 and exposed zero bodies through COM. [Source record](../../../../../re/solidworks/records/PartEnvironmentDirtyPropagation2026.md) [Native receipt](../../../../../re/solidworks/measurements/2026/PrismEnvironmentPostLoadNative01.json) [Owner update gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/Parts/EnvironmentInsertionCanDirtyOwningPart.md)
