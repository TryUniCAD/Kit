from convert.Geometry.SweptTube.BuildQuarter import BuildQuarter
from convert.Geometry.SweptTube.QuarterMetric import MeasureQuarter
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwState import (
    SwReadState,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordTopology import TopologyCounts


# native solids expose their physical topology separately from neutral periodic seam anchors
def MakeSwBody(
    StateValue: SwReadState, FeatureValue: FeatureStep, IncludeBrep: bool
) -> tuple[DesignBody, BrepModel | None]:
    IntentValue = StateValue.IntentValue
    SectionRadius = IntentValue.SectionValue.Radius * 1000.0
    PathRadius = IntentValue.PathValue.Radius * 1000.0
    MeasureValue = MeasureQuarter(SectionRadius, PathRadius)
    BodyId = f"{FeatureValue.id}:body"
    BodyValue = DesignBody(
        BodyId,
        FeatureValue.name,
        FeatureValue.id,
        topology=TopologyCounts(
            solid_count=1,
            shell_count=1,
            face_count=3,
            edge_count=2,
            vertex_count=0,
            volume=MeasureValue.VolumeValue,
            surface_area=MeasureValue.AreaValue,
            bounding_box=MeasureValue.BoundsValue,
            valid=True,
        ),
        provenance=FeatureValue.provenance,
        attributes={
            "center_of_mass_mm": (
                MeasureValue.CenterValue.x,
                MeasureValue.CenterValue.y,
                MeasureValue.CenterValue.z,
            ),
            "mass_kg": IntentValue.DensityValue * MeasureValue.VolumeValue * 1e-9,
        },
    )
    return BodyValue, (
        BuildQuarter(BodyId, SectionRadius, PathRadius) if IncludeBrep else None
    )
