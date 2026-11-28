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
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeValueFields import (
    MakeValueFields,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the text clearance is independent of the linear value and follows the signed view axis
def ChmfDistTail(PlanValue: ChmfPlan, Basis: ChmfFrame) -> dict[str, object]:
    Depth = PlanValue.SetbackValue
    IntentValue = PlanValue.DisplayValue
    Station, Clearance = (
        (1.375, PlanValue.EdgeValue.ShortSpan / 5)
        if IntentValue is None
        else IntentValue.DistanceText
    )
    SenseValue = Basis.SenseValue
    return {
        **MakeDistTail(),
        "f880": DatumPoint((0.0, SenseValue, 0.0)),
        "f8a8": Station,
        "f8b0": abs(Clearance),
        "f988": DatumPoint((Depth * SenseValue, 0.0, 0.0)),
        "f9a0": DatumPoint((Depth * SenseValue, 0.0, 0.0)),
        "fa38": DatumPoint((SenseValue, 0.0, 0.0)),
        "fad0": Depth,
    }


# linear witnesses use the physical stock axes and project into the actual display view
def MakeChmfDist(
    Feature: ArchiveNode,
    PlanValue: ChmfPlan,
    Basis: ChmfFrame,
    ViewId: int,
    DriverName: str = "D1",
) -> DimensionGraph:
    Depth = PlanValue.SetbackValue
    Frame = Basis.FrameValue
    Parameter = MakeLengthParam(Feature, Depth, DriverName)
    Dimension = MakeChmfNode(
        "ParallelPlaneDistanceDim_c", MakeValueFields(Feature, Parameter)
    )
    Dimension.FieldsValue.update(
        f80=DatumPoint(Frame.OriginValue),
        fa0=DatumPoint(Basis.EdgeCenter),
        has_fe0=1,
        fe0=DatumPoint(Frame.AxisU),
        fe8=DatumPoint(Frame.AxisV),
        has_ff0=1,
        ff0=FrameXform(Basis.ViewFrame),
    )
    Handle = MakeHandleMut(Feature, Dimension)
    Fields = MakeChmfView(Feature, Handle, ViewId, Depth, False, PlanValue.DisplayValue)
    Fields.update(ChmfDistTail(PlanValue, Basis))
    return DimensionGraph(
        Parameter, Dimension, Handle, MakeChmfNode("moDisplayDistanceDim_c", Fields)
    )
