# Sketch geometry shares line-style markers

A rectangle point pair previously looked like a circle to the marker fallback. The shared marker stores line-style fields in `sg2DEnt`, so a nearby point distance can accidentally match a linear dimension and be reported as a radius. That false circle also changes the sketch topology and derived body bounds.

For the verified current four-line sketch, use the typed point and line collections and their following empty arc count. For an actual mixed profile, keep the arc evidence and its point ownership. Coordinate coincidences alone cannot identify the primitive. [Typed offsets and verified cases](../../../../../re/solidworks/records/RectangleSketchOwners2026.md).
