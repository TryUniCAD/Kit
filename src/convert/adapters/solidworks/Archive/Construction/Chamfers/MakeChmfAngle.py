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
from convert.adapters.solidworks.Archive.Construction.Chamfers.Views.PickArcStation import (
    PickArcStation,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumOffset,
    DatumPoint,
    DatumUnit,
    KDatumVector,
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
        ff0=FrameXform(Basis.ViewFrame),
    )
    return Param, Dimension


# the exterior station follows the ordered witnesses and actual text point in the signed display frame
def ChmfAngleTail(
    Angle: float, Radius: float, SenseValue: float, Label: KDatumVector
) -> dict[str, object]:
    Direction = DatumUnit(Label)
    FirstIn = (SenseValue * Cosine(Angle), -SenseValue * SineValue(Angle), 0.0)
    OtherIn = (SenseValue, 0.0, 0.0)
    Station = PickArcStation(FirstIn, OtherIn, Direction)
    Chord = 2 * Radius * SineValue(Angle / 2)
    if Chord <= 0:
        raise ValueError("chamfer angle requires distinct ordered angular witnesses")
    return dict(
        f880=DatumPoint(Direction),
        f8a8=Station,
        f8b0=Hypot(*Label),
        fad0=Chord,
        f958=DatumPoint(
            (
                SenseValue * (Radius * -Cosine(Angle)),
                SenseValue * (Radius * SineValue(Angle)),
                0.0,
            )
        ),
        f988=DatumPoint((-SenseValue * Radius, 0.0, 0.0)),
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
    if Angle is None:
        raise ValueError("the angular chamfer display requires its actual angle")
    IntentValue = PlanValue.DisplayValue
    Radius = ShortSpan / 4 if IntentValue is None else IntentValue.WitnessLength
    Label = (
        (0.0, -ShortSpan / 3, 0.0)
        if IntentValue is None
        else (*IntentValue.AngleText, 0.0)
    )
    Param, Dimension = MakeChmfAngDim(Feature, Basis, Angle, Radius)
    Handle = MakeHandleMut(Feature, Dimension)
    Fields = MakeChmfView(Feature, Handle, ViewId, Angle, True, IntentValue)
    Fields.update(ChmfAngleTail(Angle, Radius, Basis.SenseValue, Label))
    return DimensionGraph(
        Param, Dimension, Handle, MakeChmfNode("moDisplayAngularDim_c", Fields)
    )
