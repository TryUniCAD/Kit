from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfNode,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfView import (
    MakeChmfView,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumPoint,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistTail import (
    MakeDistTail,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import (
    MakeHandleMut,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLengthParam import (
    MakeLengthParam,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeValueFields import (
    MakeValueFields,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Shells.OpenShellPlan import (
    OpenShellPlan,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import (
    PutAnnoCatalog,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# one model frame places the wall driver on the negative x side and its annotation on the cap
def MakeShellView(
    Model: ArchiveNode,
    Feature: ArchiveNode,
    HandleValue: ArchiveNode,
    Frame: PlaneFrame,
    PlanValue: OpenShellPlan,
) -> ArchiveNode:
    ViewValue = AnnoViewInput(
        "Shell Driver View", (Frame.AxisU, Frame.AxisV, Frame.NormalValue)
    )
    Views = PutAnnoCatalog(Model, 19000, (ViewValue,), None, (None,))
    ViewId = FieldInt(Views[ViewValue.NameValue].FieldsValue, "f360")
    ThicknessM = PlanValue.ThicknessM
    Stock = PlanValue.StockValue
    Origin = Frame.OriginValue
    Fields = MakeChmfView(Feature, HandleValue, ViewId, ThicknessM, False)
    Fields.update(MakeDistTail())
    Fields.update(
        f6a0={
            **RequireRecord(Fields["f6a0"]),
            "f38": MakePoint(
                XValue=Origin[0] + Stock.WidthValue / 2,
                YValue=Origin[1],
                ZValue=Stock.DepthValue,
            ),
        },
        f880=MakePoint(YValue=1.0),
        f8a8=1.25,
        f8b0=Stock.HeightValue / 10,
        f988=MakePoint(XValue=ThicknessM),
        f9a0=MakePoint(XValue=ThicknessM),
        fa38=MakePoint(XValue=1.0),
        fad0=ThicknessM,
        fb68=1,
        fb6c=1,
        ff80=0,
    )
    return MakeChmfNode("moDisplayDistanceDim_c", Fields)


# the dimension witness separation is equal to the wall thickness from the actual stock boundary
def MakeShellDim(
    Model: ArchiveNode, Feature: ArchiveNode, PlanValue: OpenShellPlan
) -> DimensionGraph:
    Stock = PlanValue.StockValue
    OuterX = min(XValue for XValue, _ in Stock.VerticesValue)
    LowerY = min(YValue for _, YValue in Stock.VerticesValue)
    CenterY = LowerY + Stock.HeightValue / 2
    Frame = PlaneFrame(
        (OuterX, CenterY, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)
    )
    Parameter = MakeLengthParam(Feature, PlanValue.ThicknessM, "D1")
    Dimension = MakeChmfNode("ThreeDRadiusDim_c", MakeValueFields(Feature, Parameter))
    Dimension.FieldsValue.update(
        f80=DatumPoint(Frame.OriginValue),
        fa0=MakePoint(XValue=OuterX + PlanValue.ThicknessM, YValue=CenterY),
        has_fe0=1,
        fe0=DatumPoint(Frame.AxisU),
        fe8=DatumPoint(Frame.AxisV),
        has_ff0=1,
        ff0=FrameXform(Frame),
    )
    HandleValue = MakeHandleMut(Feature, Dimension)
    return DimensionGraph(
        Parameter,
        Dimension,
        HandleValue,
        MakeShellView(Model, Feature, HandleValue, Frame, PlanValue),
    )
