from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from interchange.Records.RecordTopology import TopologyCounts
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)


# an existing analytic topology builder supplies validated solid geometry without emitting or attaching a native cache
def BuildPrismGeom(
    PlanValue: PrismPlan,
    BodyId: str,
    ColdValue: ColdOutput | None = None,
    *,
    CreatorValue: ArchiveNode,
) -> PartGeometry:
    LowerMm, UpperMm = (
        (-PlanValue.DepthValue, 0.0)
        if PlanValue.ReversedBlind
        else (0.0, PlanValue.DepthValue)
    )
    ModelValue, VolumeValue, AreaValue, BoundsValue = BuildPrism(
        BodyId, PlanValue.FrameValue, PlanValue.LinesValue, LowerMm, UpperMm
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
    return PartGeometry(
        ModelValue,
        TopologyValue,
        PlanValue.EvidenceValue,
        ColdValue,
        CreatorValue=CreatorValue,
    )
