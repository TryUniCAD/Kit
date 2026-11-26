# Fusion material density units use schema tokens

Fusion 2706.1.17 reports `KilogramPerCubicMeter` from `FloatProperty.units` for the tested writable `structural_Density` and `thermal_Density` properties. Passing that token to `FusionUnitsManager.convert` as a target for `kg/m^3` produced an invalid-unit error while authoring the native control. A broad presentation helper also encountered unit validation errors when inspecting the same material properties.

The [independent control helper](../../../../../re/Fusion/SavedCuboidGeneration/AuthorGenerationControl.py) recognizes the explicit kg/m³ property token and assigns a value already expressed in that unit directly. After assigning 1,175, both properties read back 1,175 and the body reported 0.001175 kg/cm³. The native mass matched density times volume. An unfamiliar property unit still requires a supported conversion or an explicit failure. This observation covers physical density. It does not qualify every property in the material or its presentation.

The [native oracle evidence](../../../../../re/Fusion/SavedCuboidGeneration/GenerationOraclePlan.md) records the failed setup, corrected control and comparison limits.
