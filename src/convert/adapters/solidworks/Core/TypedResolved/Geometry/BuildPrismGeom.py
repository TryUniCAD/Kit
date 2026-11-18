from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismGeometry import (
    PrismGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from interchange.Records.RecordTopology import TopologyCounts


# an existing analytic topology builder supplies validated solid geometry without emitting or attaching a native cache
def BuildPrismGeom(PlanValue: PrismPlan, BodyId: str) -> PrismGeometry:
    ModelValue, VolumeValue, AreaValue, BoundsValue = BuildPrism(
        BodyId, PlanValue.FrameValue, PlanValue.LinesValue, 0.0, PlanValue.DepthValue
    )
    if ModelValue.validate(frozenset((BodyId,))):
        raise ValueError("cache free prism geometry failed neutral boundary validation")
    TopologyValue = TopologyCounts(
        solid_count=len(ModelValue.bodies),
        shell_count=len(ModelValue.shells),
        face_count=len(ModelValue.faces),
        edge_count=len(ModelValue.edges),
        vertex_count=len(ModelValue.vertices),
        volume=VolumeValue,
        surface_area=AreaValue,
        bounding_box=BoundsValue,
        valid=True,
    )
    return PrismGeometry(ModelValue, TopologyValue, PlanValue.EvidenceValue)
