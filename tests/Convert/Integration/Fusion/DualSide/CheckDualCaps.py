from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import FaceCoedges
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# the physical cap carriers and outward normals must match their closed rim
def CheckDualCaps(
    State: GeometryState, Faces: tuple[FaceNode, ...], Sample: DualCase
) -> None:
    Profile = CastValue(dict[str, object], Sample.Reading["profile"])
    Center = CastValue(list[float], Profile["center_world_cm"])
    AxisValue = Sample.Frame.z_axis
    AxesValue = (AxisValue.x, AxisValue.y, AxisValue.z)
    SeenCaps: set[int] = set()
    for FaceValue in Faces:
        assert not FaceValue.DoubleSided and FaceValue.Contained is None
        Surface = State.Entities[FaceValue.Surface]
        Coedges = FaceCoedges(State, FaceValue)
        if not isinstance(Surface, PlaneNode):
            assert len(Coedges) == 2
            continue
        assert len(Coedges) == 1
        Station = sum(
            (Value - Origin) * Direction
            for Value, Origin, Direction in zip(
                Surface.OriginCm, Center, AxesValue, strict=True
            )
        )
        Lower = IsClose(Station, -Sample.SecondMm / 10, abs_tol=1e-9)
        Expected = -Sample.SecondMm / 10 if Lower else Sample.FirstMm / 10
        SeenCaps.add(-1 if Lower else 1)
        SameNumbers(
            Surface.OriginCm,
            tuple(
                Origin + Direction * Expected
                for Origin, Direction in zip(Center, AxesValue, strict=True)
            ),
        )
        Outward = sum(
            Value * Direction
            for Value, Direction in zip(Surface.Normal, AxesValue, strict=True)
        ) * (-1 if FaceValue.Reversed else 1)
        SameNumbers((Outward,), (-1.0 if Lower else 1.0,))
        EdgeValue = State.Entities[Coedges[0].EdgeRef]
        assert isinstance(EdgeValue, EdgeNode)
        Curve = State.Entities[EdgeValue.CurveRef]
        assert isinstance(Curve, EllipseNode)
        SameNumbers(Curve.OriginCm, Surface.OriginCm)
    assert SeenCaps == {-1, 1}
