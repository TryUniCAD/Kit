# Component XML rounds rigid placement

The assembly index XML represents the visible occurrence transform. Its decimal rendering can round a matrix coefficient before a new read, even when the resulting pose looks the same. In both disclosed repeated assemblies, the last component's actual `moReference_c.f360.f08.m5` and `m7` differ from their parsed XML values by one ULP. Reusing the XML values changes the Config-0 hash.

Join each indexed occurrence to its actual containing feature and target file before interpreting the transform. After the complete owner check, use the rigid matrix and translation from `f360` for the indexed occurrence. Preserve the XML values separately for inspection. Reopened publication preserves the checked basis. The ordinary neutral writer keeps its existing normalization. [Measured comparison](../../../../../../re/solidworks/records/ReopenedNestedPublication2026.md)
