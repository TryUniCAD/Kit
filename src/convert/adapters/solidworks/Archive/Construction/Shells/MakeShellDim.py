from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfNode,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumPoint,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
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
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Construction.Shells.MakeShellView import (
    MakeShellView,
)


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
