from dataclasses import dataclass as DataClass
from math import ulp as FloatUlp

from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# the analytic inward shell has independently placed outer and cavity corners
@DataClass(frozen=True, slots=True)
class ShellFootprint:
    Bounds: BoundingBox
    Thickness: float

    # one rounding budget covers the stock and cavity at their shared coordinate scale
    def CornerTolerance(self) -> float:
        Minimum, Maximum = self.Bounds.minimum, self.Bounds.maximum
        return 16 * FloatUlp(
            max(
                abs(Value)
                for Point in (Minimum, Maximum)
                for Value in (Point.x, Point.y, Point.z)
            )
        )

    # every axial station keeps a consistent cyclic order around its rectangle
    def CornerPoints(self) -> tuple[SpaceVector, ...]:
        Minimum, Maximum = self.Bounds.minimum, self.Bounds.maximum
        return tuple(
            SpaceVector(XValue, YValue, ZValue)
            for Inset, ZValue in (
                (0.0, Minimum.z),
                (0.0, Maximum.z),
                (self.Thickness, Minimum.z + self.Thickness),
                (self.Thickness, Maximum.z),
            )
            for XValue, YValue in (
                (Minimum.x + Inset, Minimum.y + Inset),
                (Maximum.x - Inset, Minimum.y + Inset),
                (Maximum.x - Inset, Maximum.y - Inset),
                (Minimum.x + Inset, Maximum.y - Inset),
            )
        )

    # an inward offset must leave a positive cavity and actual supporting floor
    def CheckInset(self) -> None:
        Minimum, Maximum = self.Bounds.minimum, self.Bounds.maximum
        if not (
            0.0 < 2 * self.Thickness < min(Maximum.x - Minimum.x, Maximum.y - Minimum.y)
            and self.Thickness < Maximum.z - Minimum.z
        ):
            raise ValueError("SOLIDWORKS shell thickness exhausts its stock")
