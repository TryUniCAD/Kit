from collections.abc import Sequence

from convert.Geometry.Parasolid import BuildPartModel
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Container.Format import KPartitionStream
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

# geometry selection uses the single local body group from configuration zero
KLocalBodyStream = "Config-0-FeatureBodies/LocalBodies"


# an empty active partition lets the single local solid supply its own complete boundary
def ReadLocalBrep(Payloads: Sequence[BrepPayload]) -> BrepModel | None:
    StreamsValue = {
        (Payload.source_stream, Payload.kind): Payload.data for Payload in Payloads
    }
    if len(Payloads) != 3 or StreamsValue.keys() != {
        (KLocalBodyStream, "unknown"),
        (KPartitionStream, "partition"),
        (KPartitionStream, "deltas"),
    }:
        return None
    LocalData = StreamsValue[(KLocalBodyStream, "unknown")]
    ActiveData = StreamsValue[(KPartitionStream, "partition")]
    HistoryData = StreamsValue[(KPartitionStream, "deltas")]
    if LocalData is None or ActiveData is None or HistoryData is None:
        return None
    try:
        ActiveNodes = ReadActiveNodes(ActiveData)
        CheckXmtGraph(ActiveNodes)
        if len(ActiveNodes) != 1 or ActiveNodes[1].Integer("body"):
            return None
        ReadXmtHistory(HistoryData, ActiveNodes)
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
