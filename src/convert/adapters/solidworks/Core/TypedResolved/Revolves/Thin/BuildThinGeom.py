from convert.Geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.Geometry.Revolve.SweepMetrics import MeasureInterval
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)
from interchange.Records.RecordTopology import TopologyCounts


# a cold thin solid is the measured annular sector from the two independently owned radii
def BuildThinGeom(OwnerValue: ThinRevOwner, BodyId: str) -> PartGeometry:
    SweepValue = OwnerValue.SweepValue
    AxisValue = SweepValue.FrameValue
    Lower, Upper = SweepValue.EndValue.IntervalValue
    Arguments = (
        OwnerValue.MeridianValue,
        AxisValue.StartValue,
        AxisValue.DirectionValue,
        AxisValue.SupportValue.x_axis,
    )
    ModelValue = BuildPolySweep(BodyId, *Arguments, Lower, Upper)
    if ModelValue.validate(frozenset((BodyId,))):
        raise ValueError(
            "SOLIDWORKS thin revolve failed the analytic boundary validation"
        )
    VolumeValue, AreaValue, BoundsValue = MeasureInterval(*Arguments, Lower, Upper)
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
        {
            "method": "typed_parametric_thin_revolve",
            "revolve_feature_id": NativeNodeId(SweepValue.NodeValue),
            "source_profile_id": NativeNodeId(SweepValue.ProfileValue),
            "wall_mode": OwnerValue.ModeValue,
        },
        ProducerValue=SweepValue.NodeValue,
    )
