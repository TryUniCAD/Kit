from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Topology.BrepTopology import BrepBody
from interchange.Records.RecordTopology import TopologyCounts


# actual use chains count each solid independently without assigning shared global topology
def StockTopCount(TopologyValue: BrepTopology, BodyValue: BrepBody) -> TopologyCounts:
    Regions = tuple(TopologyValue.regions[Value] for Value in BodyValue.region_ids)
    ShellIds = {
        TopologyValue.shell_uses[UseId].shell_id
        for Region in Regions
        for UseId in Region.shell_use_ids
    }
    FaceIds = {
        TopologyValue.face_uses[UseId].face_id
        for ShellId in ShellIds
        for UseId in TopologyValue.shells[ShellId].face_use_ids
    }
    EdgeIds = {
        TopologyValue.coedges[UseId].edge_id
        for FaceId in FaceIds
        for LoopId in TopologyValue.faces[FaceId].loop_ids
        for UseId in TopologyValue.loops[LoopId].coedge_ids
    }
    VertexIds = {
        VertexId
        for EdgeId in EdgeIds
        for VertexId in (
            TopologyValue.edges[EdgeId].start_vertex_id,
            TopologyValue.edges[EdgeId].end_vertex_id,
        )
    }
    return TopologyCounts(
        solid_count=sum(Region.solid for Region in Regions),
        shell_count=len(ShellIds),
        face_count=len(FaceIds),
        edge_count=len(EdgeIds),
        vertex_count=len(VertexIds),
    )
