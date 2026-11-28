from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordTopology import TopologyCounts


# the sole design body must belong to the final joined pattern without extra topology claims
def CheckPatResult(
    BodyValue: DesignBody, StepValue: FeatureStep, CountValue: int
) -> None:
    Expected = TopologyCounts(
        solid_count=1,
        shell_count=1,
        face_count=6 + 5 * CountValue,
        edge_count=12 + 12 * CountValue,
        vertex_count=8 + 8 * CountValue,
    )
    Topology = BodyValue.topology
    if (
        BodyValue.final_feature_id != StepValue.id
        or BodyValue.name != StepValue.name
        or BodyValue.material_id is not None
        or Topology not in (TopologyCounts(), Expected)
        or any(
            type(Amount) is not int
            for Amount in (
                Topology.solid_count,
                Topology.shell_count,
                Topology.face_count,
                Topology.edge_count,
                Topology.vertex_count,
            )
        )
    ):
        raise ValueError("final neutral body contradicts the implicit joined result")
