from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
    DatumDot,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PutHingeViews import (
    PlanHingeView,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# the signed rectangular stock projects an independently sized display onto every actual principal plane
def PutAxisViewsMut(SystemValue: PartSystem, SpansValue: KDatumVector) -> None:
    Width, Depth, Height = (RequireScalar(Value) for Value in SpansValue)
    if min(Width, Depth, Height) <= 1e-7:
        raise ValueError("principal displays require a nondegenerate signed box")
    RequireRootNode(SystemValue.RootValue, "moPart_c")
    if set(SystemValue.SystemValues.PlaneValues) != {"x", "y", "z"}:
        raise ValueError("datum sizing requires the actual three principal supports")
    Center = (Width * 0.5, -Depth * 0.5, Height * 0.5)
    Plans: list[
        tuple[ArchiveNode, ArchiveNode, dict[str, object], dict[str, float]]
    ] = []
    for AxisName in ("x", "y", "z"):
        Frame = PrincipalFrame(AxisName)
        Station = DatumDot(Center, Frame.NormalValue)
        NormalX, NormalY, NormalZ = Frame.NormalValue
        Display = (
            Center[0] - Station * NormalX,
            Center[1] - Station * NormalY,
            Center[2] - Station * NormalZ,
        )
        SpanU = DatumDot(
            SpansValue, (abs(Frame.AxisU[0]), abs(Frame.AxisU[1]), abs(Frame.AxisU[2]))
        )
        SpanV = DatumDot(
            SpansValue, (abs(Frame.AxisV[0]), abs(Frame.AxisV[1]), abs(Frame.AxisV[2]))
        )
        MarginU = SpanU * 0.5 + SpanU * 0.05
        MarginV = SpanV * 0.5 + SpanV * 0.05
        Plans.append(
            PlanHingeView(
                SystemValue, AxisName, Display, (MarginU, -MarginU, MarginV, -MarginV)
            )
        )
    for PlaneValue, DataValue, DisplayData, LabelPoint in Plans:
        DataValue.FieldsValue.update(DisplayData)
        PlaneValue.FieldsValue["f6c0"] = LabelPoint
