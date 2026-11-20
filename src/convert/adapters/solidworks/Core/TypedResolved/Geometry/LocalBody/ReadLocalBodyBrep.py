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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import (
    ReadLocalWrap,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Payloads.PayloadRecord import BrepPayload


# an empty active partition lets the single local solid supply its own complete boundary
def ReadLocalBrep(
    Payloads: Sequence[BrepPayload], GroupData: bytes, OwnerName: str
) -> BrepModel:
    LocalData, _ = ReadLocalPay(Payloads)
    if ReadLocalWrap(GroupData, LocalData) != OwnerName:
        raise ValueError("local body storage key differs from its resolved import")
    NodesValue, OffsetsValue = ReadLocalNodes(LocalData)
    CheckLocalGraph(NodesValue)
    TablesValue = MakeLocalTables(NodesValue, OffsetsValue)
    ModelValue = BuildPartModel(TablesValue)
    if (
        len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 1
        or not ModelValue.regions[0].solid
        or len(ModelValue.shells) != 1
        or not ModelValue.shells[0].closed
        or len(ModelValue.faces) != len(TablesValue.bridges)
        or len(ModelValue.loops) != len(TablesValue.loops)
        or len(ModelValue.edges) != len(TablesValue.edge_uses)
        or len(ModelValue.coedges) != len(TablesValue.coedges)
        or len(ModelValue.vertices) != len(TablesValue.vertex_uses)
        or len(ModelValue.curves) != len(TablesValue.curves)
        or len(ModelValue.surfaces) != len(TablesValue.surfaces)
        or ModelValue.validate()
    ):
        raise ValueError("local body does not contain one complete closed solid")
    return ModelValue
