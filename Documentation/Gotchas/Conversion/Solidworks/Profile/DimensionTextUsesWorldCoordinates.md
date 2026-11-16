# Radial dimension text uses world coordinates

Expectation: the radial dimension's `text_point_m` uses the same two local coordinates as its circle center.

Actual behavior: `text_point_m` is a three-dimensional world point. The existing radial builder transforms it into the sketch frame and requires its normal coordinate to be zero. In the [first end-condition generation run](https://github.com/TryUniCAD/Kit/actions/runs/43911744283/job/133455163156), the Front-plane candidate passed construction, then the Right-plane request was correctly rejected because its text point had a nonzero world X coordinate. This was an invalid neutral presentation input, not a failed native file or end-condition formula.

Use a point on the actual requested plane: world X is zero for Right, world Y for Top and world Z for Front in these admitted principal frames. Changing `plane_axis` does not implicitly transform an independently supplied world text point. The corrected requests provide explicit world points; the frame and zero-normal-coordinate guards remain unchanged. New complete generation and native outcomes require their own evidence.
