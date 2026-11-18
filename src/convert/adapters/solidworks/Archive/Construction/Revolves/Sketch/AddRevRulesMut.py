from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeAxisDim import (
    MakeAxisDim,
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
    for IndexValue in range(len(PlanValue.VerticesValue)):
        Relation = MakeAxisDim(Geometry, IndexValue)
        StartValue = PlanValue.VerticesValue[IndexValue]
        EndValue = PlanValue.VerticesValue[
            (IndexValue + 1) % len(PlanValue.VerticesValue)
        ]
        Relation["f80"] = 4 if StartValue[1] == EndValue[1] else 5
        LogicalValues.append(Relation)
    OwnerValue = ArchiveNode.RequireNode(GraphValue.ProfileValue.FieldsValue["owner"])
    PublishRectMut(
        GraphValue,
        (),
        tuple(LogicalValues),
        Allocator,
        FieldInt(OwnerValue.FieldsValue, "fd44"),
    )
