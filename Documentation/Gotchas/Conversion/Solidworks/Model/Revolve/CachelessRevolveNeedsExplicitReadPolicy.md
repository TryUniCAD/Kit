# A cache-free revolve semantic read does not establish default geometry support

The generated rectangular revolve contains its complete typed feature, angle and selected sketch-axis owners, but no transmitted Parasolid partition. A normal strict read with `include_brep=False` and `include_tessellation=False` exposes the linked `AngularRevolve` correctly. A default strict read still raises `SldprtFormat: SLDPRT contains no readable Parasolid payload`.

The separate analytic sweep used in the source-only proof is a validated neutral B-rep. It is not a stored native payload and is not attached to the generated file. Do not claim native geometry acceptance from that detached solid, and do not add an experimental generic partition to silence the reader error. The independently measured partition attachment still has a distinct warning-32 admission failure.

Keep the geometry policy explicit while examining the typed semantic construction. Qualify any future strict cache-free revolve reconstruction separately, using complete owner and feature inventory guards. Let the native oracle independently measure load, body geometry, driving edit and save/reopen before writer promotion.

[SDK revolve prototype and exact source-only evidence](../../../../../../re/solidworks/records/SdkRevolveConstruction2026.md) · [Prior partition-open diagnosis](../../../../../../re/solidworks/records/PrismPartitionOpen2026.md)
