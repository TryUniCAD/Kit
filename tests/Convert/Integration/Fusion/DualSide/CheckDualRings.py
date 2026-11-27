from math import hypot as Hypot, isclose as IsClose, tan as Tangent
from typing import cast as CastValue

from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# every native orbit must match its own independently driven end station and radius
def CheckDualRings(State: GeometryState, Sample: DualCase, EdgeCount: int) -> None:
    Rings = tuple(Value for Value in State.Entities if isinstance(Value, EllipseNode))
    assert len(Rings) == EdgeCount
    AxisValue = Sample.Frame.z_axis
    Radius = Sample.Profile.radius / 10
    Expected = (
        (
            -Sample.SecondMm / 10,
            Radius + Sample.SecondMm / 10 * Tangent(Sample.SecondTaper),
        ),
        (0.0, Radius),
        (
            Sample.FirstMm / 10,
            Radius + Sample.FirstMm / 10 * Tangent(Sample.FirstTaper),
        ),
    )
    Profile = Sample.Reading["profile"]
    assert isinstance(Profile, dict)
    Center = CastValue(list[float], Profile["center_world_cm"])
    for Curve in Rings:
        Station = sum(
            (Actual - Origin) * Direction
            for Actual, Origin, Direction in zip(
                Curve.OriginCm,
                Center,
                (AxisValue.x, AxisValue.y, AxisValue.z),
                strict=True,
            )
        )
        Match = tuple(
            Value for Value in Expected if IsClose(Station, Value[0], abs_tol=1e-9)
        )
        assert len(Match) == 1
        SameNumbers((Hypot(*Curve.MajorAxisCm), Curve.EllipseRatio), (Match[0][1], 1.0))
    assert sum(isinstance(Value, PlaneNode) for Value in State.Entities) == 2
