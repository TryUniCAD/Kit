# Empty exploded-view managers have an empty native keyword name

The normal assembly reader displays an ordinary empty exploded-view manager as `Exploded Views 1` or `Exploded Views 26`, using the actual persistent ID. The underlying `moExplViewManager_c` has a null name pointer. Its single `Feature` index row has type `Exploded Views` and an explicit empty `Name` attribute.

Build the optional manager under the actual assembly `Config-0.moAssembly_c.f1590` owner. Include its index row by actual ID and leave the resolved root sequence alone. [Pinned disclosed comparisons](../../../../../re/solidworks/records/ConcentricParentExploded2026.md)
