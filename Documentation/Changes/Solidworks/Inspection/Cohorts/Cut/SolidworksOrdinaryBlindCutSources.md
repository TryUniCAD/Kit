# Author native circular blind cut sources

The SOLIDWORKS 2026 research tool authors a rectangular boss and an eccentric
circular blind cut from separate sketches on the same principal plane. The
[source protocol](../../../../../../re/solidworks/records/OrdinaryBlindCutSource2026.md)
defines the hashed job and control inputs, three disclosed depths, and two sealed
cases with independent geometry.

The tool measures the uncut boss and the finished part. After a fresh reopen,
it changes the native driving cut depth in memory and checks body count,
volume, area, centroid and both feature definitions. It records source and
measurement hashes and requires two healthy controls.

This protocol covers a single solid body, a circular pocket strictly within
the rectangular profile, and a single blind depth from the shared sketch
plane. Python syntax, API call arity, and whitespace passed static checks.
The first oracle attempt stopped before creating the cut because the live
feature manager returned `Invalid index` for a type-information query. The
tool now resolves the interface directly from the registered 2026 library.
The repaired oracle run and source lock are pending. The tool does not deliver
a Kit writer or establish held-out writer acceptance.

[Feature manager type-information gotcha](../../../../../Gotchas/Conversion/Solidworks/Oracle/FeatureManagerDispatchCanLackTypeInfo.md)
