from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import (
    MakeLineHandle,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeAxisDim import (
    MakeAxisDim,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeBinaryDim import (
    MakeBinaryDim,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.PublishRectMut import (
    PublishRectMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# actual authored perimeter relations must update their own entity counts without adding a construction axis anchor
def AddRevRulesMut(
    GraphValue: ProfileGraph, PlanValue: RevolvePlan, Allocator: PersistentIds
) -> None:
    Geometry = RequirePolygon(GraphValue.GeometryValue)
    LogicalValues: list[dict[str, object]] = []
    for IndexValue, CodeValue in PlanValue.UnaryRules:
        Relation = MakeAxisDim(Geometry, IndexValue)
        Relation["f80"] = CodeValue
        LogicalValues.append(Relation)
    PairValues: tuple[dict[str, object], ...] = ()
    if PlanValue.EqualRule is not None:
        First, Second = PlanValue.EqualRule
        SketchValue = Geometry.SketchValue
        PairValues = (
            MakeBinaryDim(
                SketchValue,
                14,
                MakeLineHandle(SketchValue, Geometry.LineValues[First], First),
                MakeLineHandle(SketchValue, Geometry.LineValues[Second], Second),
            ),
        )
    OwnerValue = ArchiveNode.RequireNode(GraphValue.ProfileValue.FieldsValue["owner"])
    PublishRectMut(
        GraphValue,
        (),
        tuple(LogicalValues),
        Allocator,
        FieldInt(OwnerValue.FieldsValue, "fd44"),
        PairValues=PairValues,
    )
