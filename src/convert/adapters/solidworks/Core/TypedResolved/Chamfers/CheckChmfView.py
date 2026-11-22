from math import dist as Distance, isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfFrame import (
    KChmfViewName,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumOffset,
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.ReadAnnoView import (
    ReadAnnoView,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import (
    CoordsChmf,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)


# the selected carrier and its other incident face define the actual signed view axes
def ChmfViewAxes(
    PartValue: ChmfPartRead,
) -> tuple[KDatumVector, KDatumVector, KDatumVector]:
    EdgeValue = PartValue.EdgeValue
    Primary = EdgeValue.DistanceAxis
    Other = next(
        Index for Index in range(3) if Index not in (Primary, EdgeValue.EdgeAxis)
    )
    CornerBits = EdgeValue.CornerBits
    SignedU, SignedV = float(2 * CornerBits[Primary] - 1), float(
        2 * CornerBits[Other] - 1
    )
    AxisU = (
        SignedU if Primary == 0 else 0.0,
        SignedU if Primary == 1 else 0.0,
        SignedU if Primary == 2 else 0.0,
    )
    AxisV = (
        SignedV if Other == 0 else 0.0,
        SignedV if Other == 1 else 0.0,
        SignedV if Other == 2 else 0.0,
    )
    return AxisU, AxisV, CrossVector(AxisU, AxisV)


# dimension points must come from actual finite coordinates within the scoped field lookup
def ChmfViewPoint(NodeValue: ArchiveNode, FieldName: str) -> KDatumVector:
    PointValue = NativeRecord(NodeValue.FieldsValue.get(FieldName))
    return (
        RequireScalar(PointValue.get("x")),
        RequireScalar(PointValue.get("y")),
        RequireScalar(PointValue.get("z")),
    )


# the local annotation view is the actual owned frame rather than a retained external placement
def ReadChmfView(PartValue: ChmfPartRead) -> ArchiveNode:
    LinkValue = PartValue.LinkValue
    ModelValue = LinkValue.ConfigValue.RootValue
    ViewValue = ReadAnnoView(ModelValue, KChmfViewName)
    Matrix, Origin = ReadRigidXform(NativeRecord(ViewValue.FieldsValue.get("f368")))
    Expected = ChmfViewAxes(PartValue)
    AxesValue = tuple(
        (Matrix[Index], Matrix[Index + 3], Matrix[Index + 6]) for Index in range(3)
    )
    if (
        AxesValue != Expected
        or Origin != (0.0, 0.0, 0.0)
        or ModelValue.FieldsValue.get("feb0") != ViewValue.FieldsValue.get("f360")
        or NativeRecord(
            ArchiveNode.RequireNode(ModelValue.FieldsValue["fa48"]).FieldsValue
        ).get("n")
        != 1
    ):
        raise ValueError(
            "chamfer has alternate annotation catalog or signed display placement"
        )
    CheckTreeAlias(LinkValue, (ViewValue,))
    return ViewValue


# the two display witnesses bind the same finite selected edge and measured annotation intent
def CheckChmfView(PartValue: ChmfPartRead) -> None:
    ViewValue = ReadChmfView(PartValue)
    ViewId = ViewValue.FieldsValue["f360"]
    Owners = PartValue.OwnersValue
    Depth = Owners.Distance
    Angle = Owners.AngleValue
    Midpoint = CoordsChmf(PartValue.EdgeValue.EdgePoint)
    Center = (Midpoint[0] / 1000.0, Midpoint[1] / 1000.0, Midpoint[2] / 1000.0)
    AxisU, _, _ = ChmfViewAxes(PartValue)
    Anchor = DatumOffset(Center, AxisU, -Depth.ValueSi)
    if any(
        Distance(ChmfViewPoint(NodeValue, FieldName), Expected) > 1e-12
        for NodeValue, FieldName, Expected in (
            (Depth.DimensionNode, "f80", Anchor),
            (Depth.DimensionNode, "fa0", Center),
            (Angle.DimensionNode, "fc0", Anchor),
        )
    ):
        raise ValueError("chamfer display anchors differ from the actual selected edge")
    Lower = CoordsChmf(PartValue.EdgeValue.BoundsValue.minimum)
    Upper = CoordsChmf(PartValue.EdgeValue.BoundsValue.maximum)
    Width = (
        min(Second - First for First, Second in zip(Lower, Upper, strict=True)) / 1000.0
    )
    for Driver, Station, Clearance in (
        (Depth, 1.375, Width / 5),
        (Angle, -0.5, Width / 3),
    ):
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
