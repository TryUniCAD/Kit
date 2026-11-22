from math import cos as Cosine, dist as Distance, hypot as Hypot, sin as SineValue

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfFrame import (
    ChmfFrame,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import ChmfPlan
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfNode,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfView import (
    MakeChmfView,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumDot,
    DatumOffset,
    DatumPoint,
    DatumUnit,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleArc import (
    KArcTolerance,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import (
    MakeHandleMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeAngleValue import (
    MakeAngleValue,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import (
    InitNodeMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a chamfer angular parameter retains its distinct angle handle and finite model space witnesses
def MakeChmfAngDim(
    Feature: ArchiveNode, Basis: ChmfFrame, Angle: float, Radius: float
) -> tuple[ArchiveNode, ArchiveNode]:
    Frame = Basis.FrameValue
    Anchor, AxisU, AxisV = Frame.OriginValue, Frame.AxisU, Frame.AxisV
    RayValue = DatumOffset(
        DatumOffset((0.0, 0.0, 0.0), AxisU, -Cosine(Angle)), AxisV, SineValue(Angle)
    )
    First = DatumOffset(Anchor, RayValue, Radius)
    Other = DatumOffset(Anchor, AxisU, -Radius)
    if (
        First == Anchor
        or Other == Anchor
        or First == Other
        or any(
            abs(Distance(Anchor, Value) - Radius) > 1e-12 for Value in (First, Other)
        )
    ):
        raise ValueError(
            "angle requires distinct finite witnesses anchored to the actual setback"
        )
    Param = MakeChmfNode("moAngleParameter_c", {})
    InitNodeMut(Param, "D2")
    Param.FieldsValue.update(owner=Feature, f0c=0, f48=None, f58=Angle, f68=0)
    Dimension = MakeAngleValue(Feature, Param)
    Dimension.FieldsValue.update(
        f80=DatumPoint(First),
        fa0=DatumPoint(Other),
        fc0=DatumPoint(Anchor),
        has_ff0=1,
        ff0=FrameXform(Frame),
    )
    return Param, Dimension


# the independent cold arc uses its proved first exterior branch and stock relative text clearance
def ChmfAngleTail(Angle: float, ShortSpan: float, Radius: float) -> dict[str, object]:
    Label = (0.0, -ShortSpan / 3, 0.0)
    Direction = DatumUnit(Label)
    FirstIn = (Cosine(Angle), -SineValue(Angle), 0.0)
    OtherIn = (1.0, 0.0, 0.0)
    Crossing = CrossVector(FirstIn, OtherIn)
    Chord = 2 * Radius * SineValue(Angle / 2)
    if (
        Crossing[2] <= KArcTolerance
        or DatumDot(CrossVector(FirstIn, Direction), Crossing) >= -KArcTolerance
        or Chord <= 0
    ):
        raise ValueError(
            "chamfer angle label is outside the proved first-exterior witness branch"
        )
    return dict(
        f880=DatumPoint(Direction),
        f8a8=-0.5,
        f8b0=Hypot(*Label),
        fad0=Chord,
        f958=DatumPoint((Radius * -Cosine(Angle), Radius * SineValue(Angle), 0.0)),
        f988=DatumPoint((-Radius, 0.0, 0.0)),
        f100c=0,
        f1010=1,
        f1008=1,
        ffb8=DatumPoint(FirstIn),
        ffd0=DatumPoint(OtherIn),
        ffe8=-Radius,
        fff0=0.0,
        fff8=-Radius,
        f1000=0.0,
        f1018=0x18,
    )


# type specific angular display fields retain the separately editable measured view and driver
def MakeChmfAngle(
    Feature: ArchiveNode,
    PlanValue: ChmfPlan,
    Basis: ChmfFrame,
    ViewId: int,
) -> DimensionGraph:
    ShortSpan, Angle = PlanValue.EdgeValue.ShortSpan, PlanValue.AngleValue
    Radius = ShortSpan / 4
    Param, Dimension = MakeChmfAngDim(Feature, Basis, Angle, Radius)
    Handle = MakeHandleMut(Feature, Dimension)
    Fields = MakeChmfView(Feature, Handle, ViewId, Angle, True)
    Fields.update(ChmfAngleTail(Angle, ShortSpan, Radius))
    return DimensionGraph(
        Param, Dimension, Handle, MakeChmfNode("moDisplayAngularDim_c", Fields)
    )
