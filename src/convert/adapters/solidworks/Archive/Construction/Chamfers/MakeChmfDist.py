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


# the linear display derives both witness points and its first exterior label from the actual setback
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
        ff0=FrameXform(Frame),
    )
    Handle = MakeHandleMut(Feature, Dimension)
    Fields = MakeChmfView(Feature, Handle, ViewId, Depth, False)
    Fields.update(MakeDistTail())
    Fields.update(
        f880=DatumPoint((0.0, 1.0, 0.0)),
        f8a8=1.375,
        f8b0=PlanValue.EdgeValue.ShortSpan / 5,
        f988=DatumPoint((Depth, 0.0, 0.0)),
        f9a0=DatumPoint((Depth, 0.0, 0.0)),
        fa38=DatumPoint((1.0, 0.0, 0.0)),
        fad0=Depth,
    )
    return DimensionGraph(
        Parameter, Dimension, Handle, MakeChmfNode("moDisplayDistanceDim_c", Fields)
    )
