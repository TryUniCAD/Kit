# Sketch and profile archive spans have different owners

A normal typed SOLIDWORKS sketch can carry the persistent ID of its outer feature and a byte span for its inner sketch in the same record. The planar source projection's first comparison incorrectly treated the sketch's reported span as a feature span and refused.

In the previously evaluated A20/A21 source children, Sketch1 has profile persistent ID 26. The feature row's typed archive owner is `moProfileFeature_c` at map index 183. The sketch row's typed archive owner is the actual `sgSketch` at index 185, reached from the profile's `pd_f80`. Bind both spans to their actual classes and objects before traversing the indexed dimension handle. The [measured source bridge](../../../../../re/solidworks/records/SdkPlanarSourceLabelBridge2026.md) identifies the exact owner joins and the rebuilt output scope.
