# A distance mate reserves its driving dimension ID first

The ordinary distance factory creates the driving dimension before the
mate is registered. The dimension owns the first persistent ID in its
`f50` field. The mate then takes its feature ID in `f08`. Only the
registered mate receives a feature creation log.

Allocate the dimension through the shared header sequence before
registering the mate. Preserve the parameter's unassigned node ID and
store the requested length on that parameter. [Native proof and A18 readback](../../../../../re/solidworks/records/PlanarDistanceMateConstruction2026.md)
