# The part exploded-view manager has its own class

SOLIDWORKS 2026 part and assembly exploded-view managers share an empty
placement layout and use different native factories. The part factory
creates `moPrtExplViewManager_c` for the model's `f13f8` field. The
assembly factory creates `moExplViewManager_c` for `f1590`.

Bind the part keyword's ID to the actual part manager's configuration
map entry. The entry remains inherited by ResolvedFeatures. The keyword
stores an explicit empty name and the helper itself stays outside the
resolved feature roots.

[Factory and archive evidence](../../../../../re/solidworks/records/PartExplodedViewConstruction2026.md)
