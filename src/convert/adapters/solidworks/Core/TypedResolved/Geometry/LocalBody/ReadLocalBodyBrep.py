from collections.abc import Sequence

from convert.Geometry.Parasolid import BuildPartModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    ReadLocalPay,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalBodyGraph import (
    CheckLocalGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import (
    MakeLocalTables,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import (
    ReadLocalNodes,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Payloads.PayloadRecord import BrepPayload


# an empty active partition lets the single local solid supply its own complete boundary
def ReadLocalBrep(Payloads: Sequence[BrepPayload]) -> BrepModel | None:
    try:
        LocalData, _ = ReadLocalPay(Payloads)
        NodesValue, OffsetsValue = ReadLocalNodes(LocalData)
        CheckLocalGraph(NodesValue)
        TablesValue = MakeLocalTables(NodesValue, OffsetsValue)
        ModelValue = BuildPartModel(TablesValue)
    except (KeyError, OverflowError, ValueError):
        return None
    if (
        len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 1
        or len(ModelValue.faces) != len(TablesValue.bridges)
        or len(ModelValue.loops) != len(TablesValue.loops)
        or len(ModelValue.edges) != len(TablesValue.edge_uses)
        or len(ModelValue.coedges) != len(TablesValue.coedges)
        or len(ModelValue.vertices) != len(TablesValue.vertex_uses)
        or len(ModelValue.curves) != len(TablesValue.curves)
        or len(ModelValue.surfaces) != len(TablesValue.surfaces)
        or ModelValue.validate()
    ):
        return None
    return ModelValue
