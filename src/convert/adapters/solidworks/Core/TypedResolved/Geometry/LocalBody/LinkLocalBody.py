from dataclasses import replace as Replace

from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Records.RecordTopology import TopologyCounts


# the recovered solid and public design body must share ownership and counts
def LinkLocalBody(
    ModelValue: BrepModel, DesignBodyId: str
) -> tuple[BrepModel, TopologyCounts]:
    BodyValue = Replace(ModelValue.bodies[0], design_body_id=DesignBodyId)
    CountValue = TopologyCounts(
        solid_count=1,
        shell_count=len(ModelValue.shells),
        face_count=len(ModelValue.faces),
        edge_count=len(ModelValue.edges),
        vertex_count=len(ModelValue.vertices),
    )
    return Replace(ModelValue, bodies=(BodyValue,)), CountValue
