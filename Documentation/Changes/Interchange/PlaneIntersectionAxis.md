# Portable plane intersection axis

Use `interchange.PlaneAxis` or `interchange.history.PlaneAxis` to represent a finite directed reference axis from two ordered local support planes. Add it to a reference feature with the same ordered selections. Ordinary `CadDocument` JSON and mapping reads preserve the `PlaneIntersectionAxis` wire record and check both endpoints and direction against the actual support frames. This is a portable model capability. Target conversion still requires its own support.

On main baseline `b46259ae`, 25 guarded processes round-tripped two independently authored axis documents and refused 14 malformed axis inputs without runtime file reads. The pre-existing blind feature and bound plane retained identical encodings, and the invalid bound plane retained its validation result. [Feature model](../../Reference/Model/Features.md#plane-intersection-axes) · [Document integration coverage](../../../tests/Interchange/Document/PlaneAxisTests.py)
