# Shared custom mass-unit construction

The internal SOLIDWORKS part recipe accepts `UnitInput("mm", "degree", "custom", precision, "g")` or the same recipe with `"kg"`. Part preparation requires the neutral length unit to agree. The generated density record retains its own independent length format and explicit mass selection.

Six guarded builds reproduce two preset cases and both custom mass choices for two independently authored solids. Each custom Config-0 grows by 68 uncompressed bytes through its allocated length owner. Changing the mass alone alters only that stream. All six invalid modes refuse the request and all nine earlier FreeCAD box checks remain exact.

The [source measurement](../../../../../re/solidworks/measurements/2026/DocumentMassUnitsNative01.json) binds the native fields. The [construction receipt](../../../../../re/solidworks/measurements/2026/SdkCustomMassUnitConstruction01.json) records the guarded verification. The [generated lifecycle](../../../../../re/solidworks/measurements/2026/SdkCustomMassUnitsNative01.json) verifies all four exact candidates through native edit and reopen. Public registration remains open.
