# Drawing body identity needs native correspondence

A drawing-view edge can expose a live body whose self-identity is stable while direct comparison with the underlying part's body returns different. Both disclosed 2026 controls showed that exact result; all four self/repeat controls passed. The failed observer had compared objects from different domains.

Map the drawing edge through the actual underlying part's `Extension.GetCorrespondingEntity2`, validate that edge/body in the part's own inventory, then map it forward through the actual `IView.GetCorrespondingEntity`. Require supported identity within each domain and a native round trip. Keep the original drawing edge for annotation selection and persistent references. `IView.GetCorresponding` maps general objects forward and must not be used as the reverse operation.

Preserve raw cross-domain comparisons as evidence. Do not fit an equality code, substitute coordinates or count a source/API-bound predicate as native acceptance. [Exact failed measurements, 2026 contracts and frozen successor](../../../../../../re/solidworks/records/DrawingEdgeCorrespondence2026.md)
