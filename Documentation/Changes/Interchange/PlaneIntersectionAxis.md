# Portable plane intersection axis

Use `interchange.PlaneAxis` or `interchange.history.PlaneAxis` to represent a finite directed reference axis from two ordered local support planes. Add it to a reference feature with the same ordered selections. Ordinary `CadDocument` JSON and mapping reads preserve the four-field `PlaneIntersectionAxis` wire record and compare both endpoints and direction against the normalized intersection line.

Use `BoundPlaneAxis` for explicitly authored, editable extents. Its two linked signed lengths move with the selected planes. Ordinary document reads validate their ownership and recompute the finite endpoints. Native clipped axes retain their measured endpoints through `PlaneAxis`.

Forty-seven guarded processes cover millimetre, metre and inch display settings, both near-parallel direction and position counterexamples, invalid support frames, independent support and extent edits, and requests with crossed parameter owners. The pre-existing blind feature and bound plane retain identical encodings and validation behavior. [Feature model](../../Reference/Model/Features.md#plane-intersection-axes) · [Intersection regression](../../../tests/Interchange/Document/PlaneAxisNearTests.py) · [Bound extent integration](../../../tests/Interchange/Document/BoundPlaneAxisTests.py)
