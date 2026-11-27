from math import cos as Cosine, sin as SineValue

from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLabel import (
    ReadDualLabel,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import (
    BodyFaces,
    FaceCoedges,
)
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanBody import ReadSpanBody
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanCap import CheckSpanCap
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# physical carrier directions and boundary winding must agree before labels identify features
def CheckDualGeo(
    State: GeometryState,
    Shape: CircleShape,
    FirstMm: float,
    SecondMm: float,
    FirstTaper: float,
    SecondTaper: float,
) -> None:
    BodyValue, _ = ReadSpanBody(State)
    Center = (Shape.Geometry.center.x / 10, Shape.Geometry.center.y / 10)
    Radius = Shape.Geometry.radius / 10
    for FaceValue in BodyFaces(State, BodyValue):
        RoleName = ReadDualLabel(
            State, State.Entities.index(FaceValue), FirstMm, SecondMm
        )
        Surface = State.Entities[FaceValue.Surface]
        Coedges = FaceCoedges(State, FaceValue)
        if FaceValue.DoubleSided or FaceValue.Contained is not None:
            raise ValueError("Native dual side contains an unsupported sheet face")
        if isinstance(Surface, ConeNode):
            Angle = FirstTaper if RoleName == "first" else SecondTaper
            SameNumbers(Surface.OriginCm, (*Center, 0.0))
            SameNumbers(Surface.MajorAxisCm, (Radius, 0.0, 0.0))
            SameNumbers(
                (
                    Surface.EllipseRatio,
                    Surface.UScaleCm,
                    Surface.SineAngle,
                    Surface.CosineAngle,
                ),
                (1.0, Radius, SineValue(Angle), Cosine(Angle)),
            )
            if (
                FaceValue.Reversed
                or Surface.Reversed
                or len(Coedges) != 2
                or any(
                    Value is not None
                    for Value in (
                        Surface.EllipseLower,
                        Surface.EllipseUpper,
                        Surface.ULower,
                        Surface.UUpper,
                        Surface.VLower,
                        Surface.VUpper,
                    )
                )
            ):
                raise ValueError(
                    "Native dual side cone has unsupported orientation or bounds"
                )
            Required = {"joint", "rim_upper" if RoleName == "first" else "rim_lower"}
        elif isinstance(Surface, PlaneNode):
            _ = CheckSpanCap(
                Surface,
                FaceValue,
                Coedges,
                FrustumBody(
                    Shape.Geometry.radius,
                    Shape.Geometry.radius,
                    FirstMm + SecondMm,
                    (Shape.Geometry.center.x, Shape.Geometry.center.y, -SecondMm),
                ),
            )
            EdgeValue = State.Entities[Coedges[0].EdgeRef]
            if not isinstance(EdgeValue, EdgeNode) or not isinstance(
                Curve := State.Entities[EdgeValue.CurveRef], EllipseNode
            ):
                raise ValueError("Native dual side cap has no closed circular rim")
            Winding = (
                Curve.Normal[2]
                * (-1 if EdgeValue.Reversed else 1)
                * (-1 if Coedges[0].Reversed else 1)
            )
            SameNumbers((Winding,), (-1.0 if RoleName == "lower" else 1.0,))
            Required = {"rim_lower" if RoleName == "lower" else "rim_upper"}
        else:
            raise ValueError("Native dual side face has an unsupported carrier")
        if {
            ReadDualLabel(State, Coedge.EdgeRef, FirstMm, SecondMm)
            for Coedge in Coedges
        } != Required:
            raise ValueError("Native dual side face owns another physical boundary")
