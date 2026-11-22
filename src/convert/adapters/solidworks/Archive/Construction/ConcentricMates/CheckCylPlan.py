from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlacePoint import (
    PlacePoint,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# an ordinary attached child must own the coordinate frame radius and axial length selected by both mates
def CheckCylPlan(
    ChildValue: PartCandidate,
    Carrier: XmtNode,
    RimsValue: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> float:
    PlanValue = ChildValue.PlanValue
    SketchValue = ChildValue.ProfileValue.GeometryValue
    FrameValue = ChildValue.ProfileValue.FrameValue
    if (
        not isinstance(PlanValue, CirclePlan)
        or not isinstance(SketchValue, CircleGraph)
        or PlanValue.AxisValue != "z"
        or PlanValue.PlaneName != "Front Plane"
        or PlanValue.EndValue.ModeValue != "blind"
        or PlanValue.EndValue.IsReversed
        or PlanValue.SecondDepth is not None
        or ChildValue.CutValue is not None
        or ChildValue.BossValue.ProfileValue is not ChildValue.ProfileValue
    ):
        raise ValueError(
            "concentric child requires its ordinary forward blind Front circle"
        )
    Origin = ReadXmtVector(Carrier, "pvec")
    AxisValue = ReadXmtVector(Carrier, "axis")
    Radius = RequireScalar(Carrier.FieldsValue.get("radius"))
    FarValue = tuple(
        Value + AxisItem * PlanValue.DepthValue
        for Value, AxisItem in zip(Origin, AxisValue, strict=True)
    )
    if (
        AxisValue != FrameValue.NormalValue
        or Origin != PlacePoint(FrameValue, (*PlanValue.CircleValue.CenterValue, 0.0))
        or RimsValue != (Origin, FarValue)
        or not IsFinite(Radius)
        or Radius <= 0.0
        or Radius != PlanValue.CircleValue.RadiusValue
    ):
        raise ValueError(
            "concentric child carrier does not match the actual circle and blind depth"
        )
    return Radius
