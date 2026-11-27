# SOLIDWORKS empty appearance replay

The research command extracts one disclosed native save's empty appearance-manager state as canonical JSON. A fresh process uses those two typed values and independent settings to generate a version-19000 part Definition fragment. A separate command verifies the resulting wire state. [Replay guide](../../../../re/solidworks/records/ResavedRendererRead.md#replay-the-empty-allocator-in-a-fresh-definition)

The named save's present allocator value 4 survives both fresh runs and reads back as signed words `(4, 0)` with zero reference rows. The absent and present seed-one cases remain distinct. A large authored counter preserves both negative signed halves. Absence with a nondefault counter refuses before output. [Offline evidence](../../../../re/solidworks/measurements/2026/EmptyAppearanceReplay.json)

The result covers the Definition allocator fragment. Full appearance references, public conversion and native application acceptance require separate evidence. [Appearance state JSON limits](../../../Gotchas/Research/Writers/SolidworksAppearanceAllocatorRequiresExactJsonIntegers.md)
