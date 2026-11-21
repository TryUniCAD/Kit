from collections.abc import Sequence

from convert.Geometry.Parasolid import BuildPartModel
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylOwner import (
    CheckCylOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.ReadLocalCyl import (
    ReadLocalCyl,
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    ReadLocalState,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Payloads.PayloadRecord import BrepPayload


# an empty active partition lets the single local solid supply its own complete boundary
def ReadLocalBrep(
    Payloads: Sequence[BrepPayload],
    GroupData: bytes,
    OwnerName: str,
    *,
    Archive: SldprtArchive | None = None,
    OwnerValue: NativeFeature | None = None,
) -> BrepModel:
    PartitionData = Archive.get(KPartitionStream) if Archive is not None else None
    LocalData, MarkValue, PriorMark = ReadLocalState(Payloads, PartitionData)
    if ReadLocalWrap(GroupData, LocalData) != OwnerName:
        raise ValueError("local body storage key differs from its resolved import")
    NodesValue, OffsetsValue = ReadLocalNodes(
        LocalData, AllowPeriodic=Archive is not None and OwnerValue is not None
    )
    if (
        Archive is not None
        and OwnerValue is not None
        and any(NodeValue.KindValue in (31, 51) for NodeValue in NodesValue.values())
    ):
        if PartitionData is None:
            raise ValueError("local cylinder has no physical active partition")
        CheckCylOwner(Archive, OwnerValue, OwnerName, MarkValue, PriorMark)
        return ReadLocalCyl(NodesValue, OffsetsValue)
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
