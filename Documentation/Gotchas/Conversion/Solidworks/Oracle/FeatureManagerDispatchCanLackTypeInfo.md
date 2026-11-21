# Feature manager dispatch can lack type information

The blind-cut oracle obtained a working feature manager from SOLIDWORKS 2026
SP05.2 and used it to create the boss. The manager's live `IDispatch::GetTypeInfo`
returned `Invalid index` (`-2147352565`) when the oracle queried the cut
signature. Both bracketing controls were healthy. The error occurred before
the attempted cut.

Load the registered SldWorks 34.0 type library, locate `IFeatureManager` and
read the `FeatureCut4` declaration from it. Verify the library GUID, version
and ordered parameter names before using the existing feature manager to
invoke the operation. [Blind-cut source protocol](../../../../../re/solidworks/records/OrdinaryBlindCutSource2026.md)
