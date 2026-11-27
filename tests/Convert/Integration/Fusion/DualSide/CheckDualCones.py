from math import cos as Cosine, hypot as Hypot, sin as SineValue
from typing import cast as CastValue

from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# opposite cone axes retain the actual independent signed taper roles
def CheckDualCones(Cones: tuple[ConeNode, ...], Sample: DualCase) -> None:
    AxisValue = Sample.Frame.z_axis
    Center = Sample.Reading["profile"]
    assert isinstance(Center, dict)
    assert len(Cones) == 2
    Directions: set[int] = set()
    for Surface in Cones:
        Direction = sum(
            Actual * Expected
            for Actual, Expected in zip(
                Surface.AxisVector, (AxisValue.x, AxisValue.y, AxisValue.z), strict=True
            )
        )
        SignValue = 1 if Direction > 0 else -1
        Directions.add(SignValue)
        Angle = Sample.FirstTaper if SignValue == 1 else Sample.SecondTaper
        SameNumbers((Direction,), (float(SignValue),))
        SameNumbers(
            Surface.OriginCm, tuple(CastValue(list[float], Center["center_world_cm"]))
        )
        SameNumbers(
            (Hypot(*Surface.MajorAxisCm), Surface.EllipseRatio, Surface.UScaleCm),
            (Sample.Profile.radius / 10, 1.0, Sample.Profile.radius / 10),
        )
        SameNumbers(
            (Surface.SineAngle, Surface.CosineAngle), (SineValue(Angle), Cosine(Angle))
        )
    assert Directions == {-1, 1}
