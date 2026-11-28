# Saved cuboid snapshots need reciprocal ownership

The saved fixed-corner cuboid stores three snapshot roots in scan order: extrusion tool solid, profile region and sketch sheet. The Design cache serializer names the corresponding archive member and supplies passive IDs for those roots. The tool and region owners consume the first two IDs through component-scoped caches. The selected sketch consumes the third through its body identity.

A snapshot can contain the expected geometry and feature tags even if its archive name, cache collection, scope or passive root does not match the Design graph. Six controlled mutations retained lower codec readback and returned a strict read-only model before these owner links were validated. See the [ownership evidence](../../../../../../re/Fusion/SavedCuboidSnapshot/ReadbackBoundaries.md).

Require exactly one typed prism snapshot for the saved fixed-corner profile. An extra same-geometry snapshot previously bypassed checks gated on parts count. Validate the reciprocal history and cache serializer links before joining the snapshot member. Resolve the selected tool and region caches and check the passive IDs and asset/component scope. Different saves can retain different address values with the same passive root IDs. A writer still needs a measured address policy for a newly constructed graph.
