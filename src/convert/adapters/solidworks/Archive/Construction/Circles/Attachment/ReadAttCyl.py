from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylSpan import (
    CylSpan,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# the attached mantle and both rims come from the actual circle and blind extent in its selected frame
def ReadAttCyl(ChildValue: PartCandidate, PlanValue: CirclePlan) -> tuple[CylSpan, int]:
    ProfileValue = ChildValue.ProfileValue
    CircleValue = ProfileValue.GeometryValue
    if (
        not isinstance(CircleValue, CircleGraph)
        or ChildValue.BossValue.ProfileValue is not ProfileValue
    ):
        raise ValueError(
            "concentric attachment requires the actual generated circle profile"
        )
    Positions = tuple(
        RequireRecord(NodeValue.FieldsValue["pos"])
        for NodeValue in CircleValue.PointValues
    )
    Center, Marker = (
        (RequireScalar(Value["x"]), RequireScalar(Value["y"])) for Value in Positions
    )
    if (
        Center != PlanValue.CircleValue.CenterValue
        or Marker != PlanValue.CircleValue.MarkerValue
        or Center == Marker
    ):
        raise ValueError(
            "concentric attachment circle and marker differ from the modeled profile"
        )
    FrameValue = ProfileValue.FrameValue
    OriginValue, AxisValue, RadialValue = (
        FrameValue.OriginValue,
        FrameValue.NormalValue,
        FrameValue.AxisU,
    )
    XNear, YNear, ZNear = (
        PointValue + Center[0] * AlongValue + Center[1] * AcrossValue
        for PointValue, AlongValue, AcrossValue in zip(
            OriginValue, RadialValue, FrameValue.AxisV, strict=True
        )
    )
    FarXAxis, FarYAxis, FarZAxis = (
        PointValue + PlanValue.DepthValue * Direction
        for PointValue, Direction in zip((XNear, YNear, ZNear), AxisValue, strict=True)
    )
    NearValue, FarValue = (XNear, YNear, ZNear), (FarXAxis, FarYAxis, FarZAxis)
    if NearValue == FarValue or not all(map(IsFinite, (*NearValue, *FarValue))):
        raise ValueError("concentric attachment requires a finite nonzero axial extent")
    return CylSpan(
        NearValue, FarValue, AxisValue, RadialValue, PlanValue.CircleValue.RadiusValue
    ), FieldInt(CircleValue.ArcValue.FieldsValue, "f08")
