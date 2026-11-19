from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleGeomPlan import (
    CircleGeomPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from interchange.Records.RecordTopology import TopologyCounts


# the existing analytic cylinder builder supplies validated geometry without adding native kernel identities or cache payloads
def BuildCircGeom(PlanValue: CircleGeomPlan, BodyId: str) -> PartGeometry:
    RadiusValue = PlanValue.CircleValue.radius
    ModelValue, VolumeValue, AreaValue, BoundsValue = BuildCircular(
        BodyId,
        PlanValue.FrameValue,
        PlanValue.CircleValue,
        PlanValue.LowerValue,
        PlanValue.UpperValue,
        RadiusValue,
        RadiusValue,
    )
    if ModelValue.validate(frozenset((BodyId,))):
        raise ValueError(
            "cache free circle geometry failed neutral boundary validation"
        )
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
    return PartGeometry(ModelValue, TopologyValue, PlanValue.EvidenceValue)
