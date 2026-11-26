# Physical display geometry from a fresh cuboid request

[BuildLeafPlan.py](BuildLeafPlan.py) derives each face and edge bounding box from a positive origin-anchored cuboid. It uses Kit's supported constructor frame, shared geometric role tables and the canonical serializer's physical offsets. It also exposes the separate linked face-chain order.

Three independent SDK constructions used 19.3 × 27.2 × 17.4 mm, 43.7 × 12.9 × 31.4 mm and 2.54 × 8.9 × 5.3 mm. Each construction started from freshly authored specification JSON. The resulting archive was read through the strict SDK and through the typed history wire parser. All 54 generated leaf slot-to-role associations matched the actual serialized face and edge records. Each read-back volume matched its analytic dimensions and every face chain matched the role plan.

The [saved display evidence](../SavedCuboidWriter/DisplayHeightEvidence.md) establishes that the eight measured Fusion-saved scenes use their own original physical face and edge ordering. Kit's canonical serializer supplies a known independent order for fresh output. Which association the vendor uses in a loaded scene and how qualifiers participate still need the paired native tests.

The component derives geometry without a source archive, existing scene objects, a CAD runtime, or a model call. Complete display-node identities, style bindings, material and texture mapping, visibility, camera, configuration and previews remain separate dependencies. The plan does not produce a Fusion graphics scene or qualify the saved-source writer.
