from math import dist as Distance, isclose as IsClose

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfDist import (
    CheckChmfDist,
    ChmfViewPoint,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfDriver import (
    ChmfDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfViewAxes import (
    ChmfViewAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import (
    CoordsChmf,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfViews import (
    ReadChmfViews,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# chamfer labels must belong to the actual registered drive view and its documented station
def CheckChmfLabel(
    Driver: ChmfDriver, ViewId: object, Station: float, Clearance: float
) -> None:
    Fields = Driver.DisplayNode.FieldsValue
    if (
        Fields.get("n2b0") != 1
        or NativeRows(Fields.get("f2b0")) != ({"v": ViewId},)
        or Fields.get("f8a8") != Station
        or not IsClose(
            RequireScalar(Fields.get("f8b0")), Clearance, rel_tol=0.0, abs_tol=1e-12
        )
    ):
        raise ValueError(
            "chamfer has an unqualified dimension view membership or label"
        )


# active display witnesses bind the same finite edge through the incident lanes used by their mode
def CheckChmfView(PartValue: ChmfPartRead) -> None:
    Primary, *Alternates = ReadChmfViews(PartValue)
    Owners = PartValue.OwnersValue
    EdgeValue = PartValue.EdgeValue
    Midpoint = CoordsChmf(EdgeValue.EdgePoint)
    Center = (Midpoint[0] / 1000.0, Midpoint[1] / 1000.0, Midpoint[2] / 1000.0)
    Anchor = CheckChmfDist(Owners.Distance, Center, ChmfViewAxes(PartValue))
    Lower = CoordsChmf(EdgeValue.BoundsValue.minimum)
    Upper = CoordsChmf(EdgeValue.BoundsValue.maximum)
    Width = (
        min(Second - First for First, Second in zip(Lower, Upper, strict=True)) / 1000.0
    )
    ViewId = Primary.FieldsValue.get("f360")
    CheckChmfLabel(Owners.Distance, ViewId, 1.375, Width / 5)
    Angle = Owners.AngleValue
    if Angle is not None:
        if Distance(ChmfViewPoint(Angle.DimensionNode, "fc0"), Anchor) > 1e-12:
            raise ValueError(
                "chamfer angle anchor differs from the actual selected edge"
            )
        CheckChmfLabel(Angle, ViewId, -0.5, Width / 3)
    SecondValue = Owners.SecondValue
    if SecondValue is not None:
        _ = CheckChmfDist(SecondValue, Center, ChmfViewAxes(PartValue, Secondary=True))
        CheckChmfLabel(
            SecondValue, Alternates[0].FieldsValue.get("f360"), 1.375, Width / 5
        )
